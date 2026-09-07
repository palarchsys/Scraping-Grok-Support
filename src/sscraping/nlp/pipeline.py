"""Orchestration étape 2 : préfiltre → texte compressé → Grok JSON → preuves locales → SQL."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import orjson
from pydantic import ValidationError

from sscraping.db.store import Store
from sscraping.nlp.compress import compress_for_llm
from sscraping.nlp.connectors.base import LlmConnector
from sscraping.nlp.filter import might_be_crime
from sscraping.nlp.preuves import local_preuves
from sscraping.nlp.schema import IncidentExtraction
from sscraping.settings import Settings

log = logging.getLogger("sscraping.nlp")

# Prompt statique (identique à chaque appel) → cache de préfixe côté API.
SYSTEM_PROMPT = """Extracteur JSON pédagogique. N'invente rien. JSON uniquement :
{"is_crime":bool,"type_crime":null|"atteintes_vie"|"violences_personnes"|"atteintes_sexuelles"|"atteintes_biens"|"stupefiants"|"criminalite_economique"|"circulation_securite"|"ordre_public_surete","auteur":{"nom":str|null,"prenom":str|null,"nationalite":str|null,"age":int|null,"pays_origine":str|null},"faits":{"annee":int|null,"mois":int|null,"jour":int|null},"confidence":0..1}
is_crime si crime/délit de faits divers. type_crime = 1 des 8 si crime, sinon null.
Priorité type : vie > sexuel > violences > reste.
faits = date des faits (pas parution). Identité seulement si écrite. « un homme » → nulls.
confidence < 0.7 si ambigu.
"""


async def analyze_one(
    connector: LlmConnector,
    titre: str,
    texte: str,
    threshold: float,
    max_chars: int = 1800,
) -> tuple[IncidentExtraction, str]:
    if not might_be_crime(titre, texte):
        log.info("préfiltre SKIP titre=%r", titre[:80])
        ext = IncidentExtraction(is_crime=False, type_crime=None, confidence=1.0, preuves=[])
        return ext, "{}"

    user = compress_for_llm(titre, texte, max_chars=max_chars)
    log.info("préfiltre HIT titre=%r src_chars=%d prompt_chars=%d → LLM", titre[:80], len(texte), len(user))
    raw_obj: dict[str, Any] = await connector.complete_json(SYSTEM_PROMPT, user)
    raw = orjson.dumps(raw_obj).decode()
    try:
        ext = IncidentExtraction.model_validate(raw_obj)
    except ValidationError as exc:
        log.warning("JSON hors contrat: %s", exc)
        ext = IncidentExtraction(is_crime=False, type_crime=None, confidence=0.0, preuves=[])
        return ext, raw

    ext.preuves = local_preuves(titre, texte)
    if ext.confidence < threshold:
        log.info("confidence %.2f < seuil %.2f — champs extraits conservés", ext.confidence, threshold)
    return ext, raw


async def run_analyze(store: Store, connector: LlmConnector, settings: Settings) -> int:
    rows = await store.pending_analysis(limit=settings.max_articles)
    if not rows:
        log.info("rien à analyser")
        return 0
    log.info(
        "analyze batch=%d concurrency=%d model=%s",
        len(rows),
        settings.nlp_concurrency,
        connector.model,
    )
    sem = asyncio.Semaphore(max(1, settings.nlp_concurrency))

    async def _job(row: Any) -> tuple[Any, IncidentExtraction, str]:
        async with sem:
            ext, raw = await analyze_one(
                connector,
                row["titre"],
                row["texte"],
                settings.confidence_threshold,
                max_chars=settings.llm_max_chars,
            )
            return row, ext, raw

    results = await asyncio.gather(*(_job(row) for row in rows), return_exceptions=True)
    done = 0
    backend = f"{connector.name}:{connector.model}"
    for item in results:
        if isinstance(item, BaseException):
            log.exception("analyse échouée: %s", item)
            continue
        row, ext, raw = item
        if ext.is_crime:
            await store.insert_incident(row["id"], ext, backend, raw)
        await store.mark_analyzed(row["id"], backend)
        done += 1
        log.info("analyzed id=%s crime=%s type=%s", row["id"], ext.is_crime, ext.type_crime)
    grouped = await store.triage()
    log.info("triage rattachements=%d", grouped)
    return done
