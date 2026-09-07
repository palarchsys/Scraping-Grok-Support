"""Orchestration étape 2 : préfiltre → compressé → Grok (+ 1 retry JSON) → preuves locales → SQL."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import orjson
from pydantic import ValidationError

from scraping_grok.db.store import Store
from scraping_grok.nlp.compress import compress_for_llm
from scraping_grok.nlp.connectors.base import LlmConnector
from scraping_grok.nlp.filter import might_be_crime
from scraping_grok.nlp.preuves import local_preuves
from scraping_grok.nlp.schema import IncidentExtraction
from scraping_grok.settings import Settings

log = logging.getLogger("scraping_grok.nlp")

SYSTEM_PROMPT = """Extracteur JSON pédagogique. N'invente rien. JSON uniquement :
{"is_crime":bool,"type_crime":null|"atteintes_vie"|"violences_personnes"|"atteintes_sexuelles"|"atteintes_biens"|"stupefiants"|"criminalite_economique"|"circulation_securite"|"ordre_public_surete","auteurs":[{"nom":str|null,"prenom":str|null,"nationalite":str|null,"age":int|null,"pays_origine":str|null}],"lieu":str|null,"faits":{"annee":int|null,"mois":int|null,"jour":int|null},"confidence":0..1}
is_crime si crime/délit de faits divers. type_crime = 1 des 8 si crime, sinon null.
auteurs = UNIQUEMENT les mis en cause (interpellé, mis en examen, écroué, suspect nommé). PAS la victime.
Plusieurs mis en cause → plusieurs objets. « un homme » / non identifié → auteurs:[].
lieu = ville ou commune des faits si écrite, sinon null.
faits = date des faits (pas parution). Priorité type : vie > sexuel > violences > reste.
confidence < 0.7 si ambigu.
"""


async def _validate_or_retry(
    connector: LlmConnector,
    user: str,
    raw_obj: dict[str, Any],
) -> tuple[IncidentExtraction | None, dict[str, Any]]:
    try:
        return IncidentExtraction.model_validate(raw_obj), raw_obj
    except ValidationError as exc:
        log.warning("JSON hors contrat, 1 retry: %s", exc)
        fix = user + "\n\nJSON invalide, corrige uniquement le JSON:\n" + orjson.dumps(raw_obj).decode()[:800]
        raw_obj = await connector.complete_json(SYSTEM_PROMPT, fix)
        try:
            return IncidentExtraction.model_validate(raw_obj), raw_obj
        except ValidationError as exc2:
            log.warning("JSON toujours hors contrat après retry: %s", exc2)
            return None, raw_obj


async def analyze_one(
    connector: LlmConnector,
    titre: str,
    texte: str,
    threshold: float,
    max_chars: int = 1800,
) -> tuple[IncidentExtraction, str, str]:
    """Retourne (extraction, raw_json, analyze_status)."""
    if not might_be_crime(titre, texte):
        log.info("préfiltre SKIP titre=%r", titre[:80])
        ext = IncidentExtraction(is_crime=False, type_crime=None, confidence=1.0, preuves=[])
        return ext, "{}", "ignored"

    user = compress_for_llm(titre, texte, max_chars=max_chars)
    log.info("préfiltre HIT titre=%r src_chars=%d prompt_chars=%d → LLM", titre[:80], len(texte), len(user))
    raw_obj: dict[str, Any] = await connector.complete_json(SYSTEM_PROMPT, user)
    ext, raw_obj = await _validate_or_retry(connector, user, raw_obj)
    raw = orjson.dumps(raw_obj).decode()
    if ext is None:
        ext = IncidentExtraction(is_crime=False, type_crime=None, confidence=0.0, preuves=[])
        return ext, raw, "error"

    ext.preuves = local_preuves(titre, texte)
    if ext.confidence < threshold:
        log.info("confidence %.2f < seuil %.2f — champs extraits conservés", ext.confidence, threshold)
    return ext, raw, ("extracted" if ext.is_crime else "ignored")


async def run_analyze(store: Store, connector: LlmConnector, settings: Settings) -> int:
    rows = await store.pending_analysis(limit=settings.max_articles)
    if not rows:
        log.info("rien à analyser (pending=0, ignored non retraités)")
        return 0
    log.info(
        "analyze batch=%d concurrency=%d model=%s",
        len(rows),
        settings.nlp_concurrency,
        connector.model,
    )
    sem = asyncio.Semaphore(max(1, settings.nlp_concurrency))

    async def _job(row: Any) -> tuple[Any, IncidentExtraction, str, str]:
        async with sem:
            ext, raw, status = await analyze_one(
                connector,
                row["titre"],
                row["texte"],
                settings.confidence_threshold,
                max_chars=settings.llm_max_chars,
            )
            return row, ext, raw, status

    results = await asyncio.gather(*(_job(row) for row in rows), return_exceptions=True)
    done = 0
    backend = f"{connector.name}:{connector.model}"
    for item in results:
        if isinstance(item, BaseException):
            log.exception("analyse échouée: %s", item)
            continue
        row, ext, raw, status = item
        if ext.is_crime:
            await store.insert_incident(row["id"], ext, backend, raw, titre=row["titre"])
        await store.mark_analyzed(row["id"], backend, status)
        done += 1
        log.info("analyzed id=%s status=%s crime=%s type=%s", row["id"], status, ext.is_crime, ext.type_crime)
    grouped = await store.triage()
    log.info("triage rattachements=%d", grouped)
    usage = getattr(connector, "usage", None)
    if usage:
        log.info("tokens %s", usage)
    return done
