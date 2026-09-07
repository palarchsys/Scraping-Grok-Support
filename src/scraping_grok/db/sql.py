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
WHERE statut = 'ok'
  AND analyze_status = 'pending'
  AND analyzed_at IS NULL
  AND length(texte) > 40
ORDER BY id DESC
LIMIT %s
"""

KNOWN_URLS = "SELECT url FROM articles"

MARK_ANALYZED = """
UPDATE articles
SET analyzed_at = now(), analyze_backend = %s, analyze_status = %s
WHERE id = %s AND analyze_status = 'pending'
"""

UPSERT_INCIDENT = """
INSERT INTO incidents (
  article_id, is_crime, type_crime, nom, prenom, nationalite, age, pays_origine, lieu, auteurs,
  annee, mois, jour, confidence, preuves, modele_version, raw_model_output
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (article_id) DO UPDATE SET
  is_crime = EXCLUDED.is_crime,
  type_crime = EXCLUDED.type_crime,
  nom = EXCLUDED.nom,
  prenom = EXCLUDED.prenom,
  nationalite = EXCLUDED.nationalite,
  age = EXCLUDED.age,
  pays_origine = EXCLUDED.pays_origine,
  lieu = EXCLUDED.lieu,
  auteurs = EXCLUDED.auteurs,
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

INSERT_FAIT = """
INSERT INTO faits (nom_norm, prenom_norm, lieu_norm, titre_norm, annee, mois, jour, type_crime, article_id_principal)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
RETURNING id
"""

FIND_FAITS_DATE = """
SELECT id, nom_norm, prenom_norm, lieu_norm, titre_norm, annee, mois, jour
FROM faits
WHERE annee IS NOT NULL AND mois IS NOT NULL AND jour IS NOT NULL
  AND make_date(annee, mois, jour) BETWEEN %s AND %s
"""

ATTACH_FAIT = "UPDATE incidents SET fait_id = %s WHERE id = %s"

UNGROUPED = """
SELECT i.id, i.article_id, i.nom, i.prenom, i.lieu, i.auteurs, i.annee, i.mois, i.jour, i.type_crime, a.titre
FROM incidents i
JOIN articles a ON a.id = i.article_id
WHERE i.is_crime = true
"""
