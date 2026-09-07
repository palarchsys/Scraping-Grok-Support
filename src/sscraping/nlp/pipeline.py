"""Orchestration étape 2 : préfiltre → LLM JSON → Pydantic → SQL."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import orjson
from pydantic import ValidationError

from sscraping.db.store import Store
from sscraping.nlp.connectors.base import LlmConnector
from sscraping.nlp.filter import might_be_aggression
from sscraping.nlp.schema import IncidentExtraction
from sscraping.settings import Settings

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tu es un extracteur JSON pour un exercice pédagogique.
Tu lis UN article de presse. Tu ne juges pas, tu n'inventes pas.
Réponds UNIQUEMENT un objet JSON de ce schéma :
{
  "is_aggression": boolean,
  "categorie": "non_agression"|"violence_physique"|"agression_sexuelle"|"homicide"|"tentative"|"menace"|"vol_avec_violence"|"autre_agression",
  "agresseur": {
    "nom": string|null,
    "prenom": string|null,
    "nationalite": string|null,
    "age": int|null,
    "pays_origine": string|null
  },
  "faits": {"annee": int|null, "mois": int|null, "jour": int|null},
  "confidence": number,
  "preuves": string[]
}
Règles :
- is_aggression=true seulement si l'article décrit une agression / infraction violente (pas un débat, un match, une métaphore).
- Date = date des FAITS, pas la date de publication, pas l'audience.
- nationalite / pays_origine : uniquement si le texte les écrit clairement. Sinon null. Interdit d'inférer.
- nom/prenom : seulement si identifiés. « un homme » → tout null.
- confidence < 0.7 si le texte est ambigu (victime vs auteur, plusieurs personnes).
- preuves : 1 à 3 citations courtes copiées du texte.
"""


def _user_payload(titre: str, texte: str, max_chars: int) -> str:
    body = texte[:max_chars]
    return f"TITRE: {titre}\n\nTEXTE:\n{body}"


async def analyze_one(
    connector: LlmConnector,
    titre: str,
    texte: str,
    threshold: float,
    max_chars: int = 8000,
) -> tuple[IncidentExtraction, str]:
    if not might_be_aggression(titre, texte):
        ext = IncidentExtraction(is_aggression=False, categorie="non_agression", confidence=1.0, preuves=[])
        return ext, "{}"

    raw_obj: dict[str, Any] = await connector.complete_json(
        SYSTEM_PROMPT,
        _user_payload(titre, texte, max_chars),
    )
    raw = orjson.dumps(raw_obj).decode()
    try:
        ext = IncidentExtraction.model_validate(raw_obj)
    except ValidationError as exc:
        log.warning("JSON hors contrat: %s", exc)
        ext = IncidentExtraction(is_aggression=False, categorie="non_agression", confidence=0.0, preuves=[])
        return ext, raw

    if ext.confidence < threshold:
        ext.agresseur.nom = None
        ext.agresseur.prenom = None
        ext.agresseur.nationalite = None
        ext.agresseur.age = None
        ext.agresseur.pays_origine = None
        if ext.categorie != "non_agression" and ext.confidence < 0.4:
            ext.is_aggression = False
            ext.categorie = "non_agression"
    return ext, raw


async def run_analyze(store: Store, connector: LlmConnector, settings: Settings) -> int:
    """LLM en parallèle (nlp_concurrency), écritures SQLite en série."""
    rows = await store.pending_analysis(limit=settings.max_articles)
    if not rows:
        return 0
    sem = asyncio.Semaphore(max(1, settings.nlp_concurrency))

    async def _job(row: Any) -> tuple[Any, IncidentExtraction, str]:
        async with sem:
            ext, raw = await analyze_one(
                connector,
                row["titre"],
                row["texte"],
                settings.confidence_threshold,
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
        if ext.is_aggression:
            await store.insert_incident(row["id"], ext, backend, raw)
        await store.mark_analyzed(row["id"], backend)
        done += 1
        log.info("analyzed id=%s aggression=%s cat=%s", row["id"], ext.is_aggression, ext.categorie)
    return done
