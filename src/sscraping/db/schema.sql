PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  titre TEXT NOT NULL,
  texte TEXT NOT NULL DEFAULT '',
  date_publication TEXT,
  scraped_at TEXT NOT NULL,
  statut TEXT NOT NULL DEFAULT 'ok',
  error TEXT,
  analyzed_at TEXT,
  analyze_backend TEXT
);

CREATE INDEX IF NOT EXISTS idx_articles_analyzed ON articles(analyzed_at);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);

CREATE TABLE IF NOT EXISTS incidents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  categorie TEXT NOT NULL,
  -- Identités en clair telles qu'extraites de l'article. NULL = absent du texte.
  -- Aucun masquage SQL : le masquage est un souci d'affichage GUI (hors de ce dépôt).
  nom TEXT,
  prenom TEXT,
  nationalite TEXT,
  age INTEGER,
  pays_origine TEXT,
  annee INTEGER,
  mois INTEGER,
  jour INTEGER,
  confidence REAL NOT NULL,
  preuves TEXT NOT NULL DEFAULT '[]',
  modele_version TEXT NOT NULL,
  raw_model_output TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_incidents_article ON incidents(article_id);
