"""Accès SQL async. aiosqlite + WAL = un process, des milliers d'upserts/s largement assez."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from sscraping.nlp.schema import IncidentExtraction
from sscraping.scrape.base import ScrapedArticle

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._db: aiosqlite.Connection | None = None

    async def open(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        assert self._db is not None
        return self._db

    async def upsert_article(self, art: ScrapedArticle) -> int:
        """INSERT ON CONFLICT(url) : on ne réécrit le texte que s'il est plus long (HTML > résumé)."""
        date = art.date_publication.isoformat() if art.date_publication else None
        cur = await self.db.execute(
            """
            INSERT INTO articles (source, url, titre, texte, date_publication, scraped_at, statut, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
              titre=excluded.titre,
              texte=CASE WHEN length(excluded.texte) > length(articles.texte) THEN excluded.texte ELSE articles.texte END,
              date_publication=COALESCE(excluded.date_publication, articles.date_publication),
              statut=excluded.statut,
              error=excluded.error
            RETURNING id
            """,
            (art.source, art.url, art.titre, art.texte, date, _now(), art.statut, art.error),
        )
        row = await cur.fetchone()
        await self.db.commit()
        return int(row["id"])

    async def pending_analysis(self, limit: int = 200) -> list[aiosqlite.Row]:
        cur = await self.db.execute(
            """
            SELECT * FROM articles
            WHERE statut='ok' AND analyzed_at IS NULL AND length(texte) > 40
            ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        )
        return await cur.fetchall()

    async def mark_analyzed(self, article_id: int, backend: str) -> None:
        await self.db.execute(
            "UPDATE articles SET analyzed_at=?, analyze_backend=? WHERE id=?",
            (_now(), backend, article_id),
        )
        await self.db.commit()

    async def insert_incident(
        self,
        article_id: int,
        ext: IncidentExtraction,
        backend: str,
        raw: str,
    ) -> None:
        if not ext.is_aggression:
            return
        # Champs auteur : valeurs extraites, éventuellement NULL. Pas de masquage.
        await self.db.execute(
            """
            INSERT INTO incidents (
              article_id, categorie, nom, prenom, nationalite, age, pays_origine,
              annee, mois, jour, confidence, preuves, modele_version, raw_model_output, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                article_id,
                ext.categorie,
                ext.agresseur.nom,
                ext.agresseur.prenom,
                ext.agresseur.nationalite,
                ext.agresseur.age,
                ext.agresseur.pays_origine,
                ext.faits.annee,
                ext.faits.mois,
                ext.faits.jour,
                ext.confidence,
                json.dumps(ext.preuves, ensure_ascii=False),
                backend,
                raw,
                _now(),
            ),
        )
        await self.db.commit()

    async def counts(self) -> dict[str, int]:
        arts = await (await self.db.execute("SELECT COUNT(*) n FROM articles")).fetchone()
        inc = await (await self.db.execute("SELECT COUNT(*) n FROM incidents")).fetchone()
        pending = await (
            await self.db.execute("SELECT COUNT(*) n FROM articles WHERE analyzed_at IS NULL AND statut='ok'")
        ).fetchone()
        return {"articles": arts["n"], "incidents": inc["n"], "pending": pending["n"]}
