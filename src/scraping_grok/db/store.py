"""Accès PostgreSQL async (psycopg). Identités stockées en clair. Jamais de retraitement ignored."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from scraping_grok.db import sql as Q
from scraping_grok.nlp.schema import IncidentExtraction
from scraping_grok.scrape.base import ScrapedArticle

log = logging.getLogger("scraping_grok.sql")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")

MIGRATIONS = [
    "ALTER TABLE articles ADD COLUMN IF NOT EXISTS analyze_status TEXT NOT NULL DEFAULT 'pending'",
    """
    UPDATE articles SET analyze_status = 'extracted'
    WHERE analyze_status = 'pending' AND id IN (SELECT article_id FROM incidents)
    """,
    """
    UPDATE articles SET analyze_status = 'ignored'
    WHERE analyzed_at IS NOT NULL AND analyze_status = 'pending'
    """,
    "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS lieu TEXT",
    "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS auteurs TEXT NOT NULL DEFAULT '[]'",
    "ALTER TABLE faits ADD COLUMN IF NOT EXISTS lieu_norm TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE faits ADD COLUMN IF NOT EXISTS titre_norm TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE faits ALTER COLUMN nom_norm SET DEFAULT ''",
    "ALTER TABLE faits ALTER COLUMN prenom_norm SET DEFAULT ''",
    "ALTER TABLE faits ALTER COLUMN annee DROP NOT NULL",
    "ALTER TABLE faits ALTER COLUMN mois DROP NOT NULL",
    "ALTER TABLE faits ALTER COLUMN jour DROP NOT NULL",
    "ALTER TABLE faits DROP CONSTRAINT IF EXISTS faits_nom_norm_prenom_norm_annee_mois_jour_key",
]


def _split_sql(blob: str) -> list[str]:
    stmts: list[str] = []
    buf: list[str] = []
    for line in blob.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buf.append(line)
        if stripped.endswith(";"):
            stmts.append("\n".join(buf).strip())
            buf = []
    return stmts


class Store:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._conn: AsyncConnection | None = None

    async def open(self) -> None:
        log.debug("connect %s", _redact_dsn(self._dsn))
        self._conn = await AsyncConnection.connect(self._dsn, row_factory=dict_row)
        await self.init_schema()

    async def init_schema(self) -> None:
        assert self._conn is not None
        raw = SCHEMA_PATH.read_text(encoding="utf-8")
        for stmt in _split_sql(raw):
            log.debug("DDL %s", stmt.split()[0:4])
            await self._conn.execute(stmt)
        await self._conn.commit()
        for stmt in MIGRATIONS:
            try:
                await self._conn.execute(stmt)
                await self._conn.commit()
            except Exception as exc:  # noqa: BLE001
                log.debug("migration skip %s (%s)", " ".join(stmt.split())[:80], exc)
                await self._conn.rollback()
        log.info("schema OK")

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None
            log.debug("connection closed")

    @property
    def db(self) -> AsyncConnection:
        assert self._conn is not None
        return self._conn

    async def upsert_article(self, art: ScrapedArticle) -> int:
        log.debug(
            "UPSERT article source=%s url=%s titre=%r chars=%d statut=%s",
            art.source,
            art.url,
            art.titre[:80],
            len(art.texte or ""),
            art.statut,
        )
        cur = await self.db.execute(
            Q.UPSERT_ARTICLE,
            (art.source, art.url, art.titre, art.texte, art.date_publication, art.statut, art.error),
        )
        row = await cur.fetchone()
        await self.db.commit()
        article_id = int(row["id"])
        log.info("article id=%s url=%s", article_id, art.url)
        return article_id

    async def pending_analysis(self, limit: int = 200) -> list[dict]:
        cur = await self.db.execute(Q.PENDING, (limit,))
        rows = await cur.fetchall()
        log.info("pending analysis=%d limit=%d", len(rows), limit)
        return list(rows)

    async def mark_analyzed(self, article_id: int, backend: str, status: str) -> None:
        """status: ignored | extracted | error. No-op si déjà traité (pending seulement)."""
        log.debug("MARK analyzed id=%s backend=%s status=%s", article_id, backend, status)
        cur = await self.db.execute(Q.MARK_ANALYZED, (backend, status, article_id))
        n = cur.rowcount if cur is not None else 0
        await self.db.commit()
        if not n:
            log.info("SKIP reprocess id=%s déjà traité (pas pending)", article_id)

    async def _attach_fait(
        self,
        incident_id: int,
        article_id: int,
        ext: IncidentExtraction,
        titre: str = "",
    ) -> int | None:
        from scraping_grok.nlp.group import (
            date_window,
            event_date,
            named_auteurs,
            norm_name,
            titles_similar,
            titre_norm,
        )

        d = event_date(ext)
        if not d:
            log.debug("groupage impossible incident=%s (date incomplète)", incident_id)
            return None
        lieu = norm_name(ext.lieu) or ""
        tnorm = titre_norm(titre)
        people = named_auteurs(ext)
        lo, hi = date_window(d)
        cur = await self.db.execute(Q.FIND_FAITS_DATE, (lo, hi))
        rows = await cur.fetchall()
        match_id: int | None = None
        for row in rows:
            other_lieu = row["lieu_norm"] or ""
            if lieu and other_lieu and lieu != other_lieu:
                continue
            if people:
                person = (row["nom_norm"] or "", row["prenom_norm"] or "")
                if person in people or (person == ("", "") and titles_similar(tnorm, row["titre_norm"] or "")):
                    match_id = int(row["id"])
                    break
            elif titles_similar(tnorm, row["titre_norm"] or ""):
                match_id = int(row["id"])
                break
        if match_id is None:
            nom, prenom = people[0] if people else ("", "")
            cur = await self.db.execute(
                Q.INSERT_FAIT,
                (nom, prenom, lieu, tnorm, d.year, d.month, d.day, ext.type_crime, article_id),
            )
            match_id = int((await cur.fetchone())["id"])
            log.info("fait nouveau id=%s %s %s %s %s", match_id, prenom, nom, lieu, d)
        await self.db.execute(Q.ATTACH_FAIT, (match_id, incident_id))
        log.info("fait id=%s incident=%s", match_id, incident_id)
        return match_id

    async def insert_incident(
        self,
        article_id: int,
        ext: IncidentExtraction,
        backend: str,
        raw: str,
        titre: str = "",
    ) -> None:
        if not ext.is_crime:
            log.debug("skip incident id=%s is_crime=false", article_id)
            return
        principal = ext.auteur
        log.info(
            "UPSERT incident article_id=%s type=%s auteurs=%d lieu=%s conf=%.2f",
            article_id,
            ext.type_crime,
            len(ext.auteurs) or 1,
            ext.lieu,
            ext.confidence,
        )
        cur = await self.db.execute(
            Q.UPSERT_INCIDENT,
            (
                article_id,
                ext.is_crime,
                ext.type_crime,
                principal.nom,
                principal.prenom,
                principal.nationalite,
                principal.age,
                principal.pays_origine,
                ext.lieu,
                json.dumps([a.model_dump() for a in (ext.auteurs or [principal])], ensure_ascii=False),
                ext.faits.annee,
                ext.faits.mois,
                ext.faits.jour,
                ext.confidence,
                json.dumps(ext.preuves, ensure_ascii=False),
                backend,
                raw,
            ),
        )
        inc = await cur.fetchone()
        incident_id = int(inc["id"])
        await self._attach_fait(incident_id, article_id, ext, titre=titre)
        await self.db.commit()

    async def triage(self) -> int:
        from scraping_grok.nlp.schema import Auteur, Faits, IncidentExtraction

        rows = await (await self.db.execute(Q.UNGROUPED)).fetchall()
        n = 0
        for row in rows:
            raw_auteurs = []
            try:
                raw_auteurs = json.loads(row.get("auteurs") or "[]")
            except json.JSONDecodeError:
                raw_auteurs = []
            auteurs = [Auteur.model_validate(x) for x in raw_auteurs] if raw_auteurs else []
            ext = IncidentExtraction(
                is_crime=True,
                type_crime=row["type_crime"],
                auteur=Auteur(nom=row["nom"], prenom=row["prenom"]),
                auteurs=auteurs,
                lieu=row.get("lieu"),
                faits=Faits(annee=row["annee"], mois=row["mois"], jour=row["jour"]),
                confidence=1.0,
            )
            if await self._attach_fait(int(row["id"]), int(row["article_id"]), ext, titre=row.get("titre") or ""):
                n += 1
        await self.db.commit()
        log.info("triage incidents rattachés=%d / %d", n, len(rows))
        return n

    async def counts(self) -> dict[str, int]:
        arts = (await (await self.db.execute("SELECT COUNT(*) AS n FROM articles")).fetchone())["n"]
        inc = (await (await self.db.execute("SELECT COUNT(*) AS n FROM incidents")).fetchone())["n"]
        pending = (
            await (
                await self.db.execute(
                    "SELECT COUNT(*) AS n FROM articles WHERE analyze_status='pending' AND statut='ok'"
                )
            ).fetchone()
        )["n"]
        ignored = (
            await (
                await self.db.execute("SELECT COUNT(*) AS n FROM articles WHERE analyze_status='ignored'")
            ).fetchone()
        )["n"]
        faits = (await (await self.db.execute("SELECT COUNT(*) AS n FROM faits")).fetchone())["n"]
        multi = (
            await (
                await self.db.execute(
                    """
                    SELECT COUNT(*) AS n FROM (
                      SELECT fait_id FROM incidents
                      WHERE fait_id IS NOT NULL
                      GROUP BY fait_id HAVING COUNT(*) > 1
                    ) t
                    """
                )
            ).fetchone()
        )["n"]
        out = {
            "articles": int(arts),
            "incidents": int(inc),
            "pending": int(pending),
            "ignored": int(ignored),
            "faits": int(faits),
            "faits_multi": int(multi),
        }
        log.info("counts %s", out)
        return out


def _redact_dsn(dsn: str) -> str:
    if "@" not in dsn or "://" not in dsn:
        return dsn
    head, tail = dsn.split("://", 1)
    if "@" in tail and ":" in tail.split("@", 1)[0]:
        user = tail.split(":", 1)[0]
        rest = tail.split("@", 1)[1]
        return f"{head}://{user}:***@{rest}"
    return dsn
