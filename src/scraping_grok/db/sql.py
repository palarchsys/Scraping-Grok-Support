"""SQL partagé Scrapy (sync) / Store (async). Placeholders psycopg %s."""

UPSERT_ARTICLE = """
INSERT INTO articles (source, url, titre, texte, date_publication, statut, error)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (url) DO UPDATE SET
  titre = EXCLUDED.titre,
  texte = CASE
    WHEN length(EXCLUDED.texte) > length(articles.texte) THEN EXCLUDED.texte
    ELSE articles.texte
  END,
  date_publication = COALESCE(EXCLUDED.date_publication, articles.date_publication),
  statut = EXCLUDED.statut,
  error = EXCLUDED.error,
  scraped_at = now()
RETURNING id
"""

PENDING = """
SELECT id, source, url, titre, texte, date_publication
FROM articles
WHERE statut = 'ok' AND analyzed_at IS NULL AND length(texte) > 40
ORDER BY id DESC
LIMIT %s
"""

KNOWN_URLS = "SELECT url FROM articles"

MARK_ANALYZED = """
UPDATE articles SET analyzed_at = now(), analyze_backend = %s WHERE id = %s
"""

UPSERT_INCIDENT = """
INSERT INTO incidents (
  article_id, is_crime, type_crime, nom, prenom, nationalite, age, pays_origine,
  annee, mois, jour, confidence, preuves, modele_version, raw_model_output
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (article_id) DO UPDATE SET
  is_crime = EXCLUDED.is_crime,
  type_crime = EXCLUDED.type_crime,
  nom = EXCLUDED.nom,
  prenom = EXCLUDED.prenom,
  nationalite = EXCLUDED.nationalite,
  age = EXCLUDED.age,
  pays_origine = EXCLUDED.pays_origine,
  annee = EXCLUDED.annee,
  mois = EXCLUDED.mois,
  jour = EXCLUDED.jour,
  confidence = EXCLUDED.confidence,
  preuves = EXCLUDED.preuves,
  modele_version = EXCLUDED.modele_version,
  raw_model_output = EXCLUDED.raw_model_output,
  created_at = now()
RETURNING id
"""

UPSERT_FAIT = """
INSERT INTO faits (nom_norm, prenom_norm, annee, mois, jour, type_crime, article_id_principal)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (nom_norm, prenom_norm, annee, mois, jour) DO UPDATE SET
  type_crime = COALESCE(faits.type_crime, EXCLUDED.type_crime)
RETURNING id
"""

ATTACH_FAIT = "UPDATE incidents SET fait_id = %s WHERE id = %s"

UNGROUPED = """
SELECT id, article_id, nom, prenom, annee, mois, jour, type_crime
FROM incidents
WHERE is_crime = true
"""
