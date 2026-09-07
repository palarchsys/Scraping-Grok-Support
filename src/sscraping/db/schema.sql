-- PostgreSQL. Identités en clair. Un fait = nom+prénom+date (triage anti-doublon).

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

CREATE TABLE IF NOT EXISTS faits (
  id BIGSERIAL PRIMARY KEY,
  nom_norm TEXT NOT NULL,
  prenom_norm TEXT NOT NULL,
  annee INTEGER NOT NULL,
  mois INTEGER NOT NULL,
  jour INTEGER NOT NULL,
  type_crime TEXT,
  article_id_principal BIGINT REFERENCES articles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (nom_norm, prenom_norm, annee, mois, jour)
);

CREATE TABLE IF NOT EXISTS incidents (
  id BIGSERIAL PRIMARY KEY,
  article_id BIGINT NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
  fait_id BIGINT REFERENCES faits(id) ON DELETE SET NULL,
  is_crime BOOLEAN NOT NULL DEFAULT true,
  type_crime TEXT NOT NULL,
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
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT incidents_type_crime_chk CHECK (type_crime IN (
    'atteintes_vie',
    'violences_personnes',
    'atteintes_sexuelles',
    'atteintes_biens',
    'stupefiants',
    'criminalite_economique',
    'circulation_securite',
    'ordre_public_surete'
  ))
);

CREATE INDEX IF NOT EXISTS idx_incidents_article ON incidents (article_id);
CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents (type_crime);
CREATE INDEX IF NOT EXISTS idx_incidents_fait ON incidents (fait_id);
