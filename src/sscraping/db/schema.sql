-- PostgreSQL. Identités en clair dans incidents (pas de masquage SQL).

CREATE TABLE IF NOT EXISTS articles (
  id BIGSERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  titre TEXT NOT NULL,
  texte TEXT NOT NULL DEFAULT '',
  date_publication TIMESTAMPTZ,
  scraped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  statut TEXT NOT NULL DEFAULT 'ok',
  error TEXT,
  analyzed_at TIMESTAMPTZ,
  analyze_backend TEXT
);

CREATE INDEX IF NOT EXISTS idx_articles_analyzed ON articles (analyzed_at);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles (source);

CREATE TABLE IF NOT EXISTS incidents (
  id BIGSERIAL PRIMARY KEY,
  article_id BIGINT NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
  categorie TEXT NOT NULL,
  -- Identités en clair telles qu'extraites. NULL = absent du texte.
  nom TEXT,
  prenom TEXT,
  nationalite TEXT,
  age INTEGER,
  pays_origine TEXT,
  annee INTEGER,
  mois INTEGER,
  jour INTEGER,
  confidence DOUBLE PRECISION NOT NULL,
  preuves TEXT NOT NULL DEFAULT '[]',
  modele_version TEXT NOT NULL,
  raw_model_output TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_incidents_article ON incidents (article_id);
