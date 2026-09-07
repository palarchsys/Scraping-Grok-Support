# Étape 2 NLP — contrat court

Entrée : articles `statut=ok` non analysés. Sortie : `incidents` + `articles.analyzed_at`.

## 8 groupes `type_crime` (fermés, partition des faits divers)
atteintes_vie | violences_personnes | atteintes_sexuelles | atteintes_biens | stupefiants | criminalite_economique | circulation_securite | ordre_public_surete

Hors crime : `is_crime=false`, `type_crime=null` — pas de ligne incidents.

## Flux
`prefilter → si miss: skip → connector.complete_json → IncidentExtraction.model_validate → store (identités en clair)`

LLM parallèle (`NLP_CONCURRENCY`, défaut 4). Writes PostgreSQL en série. Logs DEBUG → `logs/nlp.log`.

## Extraction
`type_crime` obligatoire si crime (un des 8). Champs auteur/date : **valeurs de l’article**, NULL si non écrits. Jamais d’inférence. Jamais de masquage en base. `confidence` est un score, pas un filtre destructif. Masquage = GUI hors dépôt.

## Connecteurs
Interface `LlmConnector.complete_json(system, user) -> dict`.
Implémentation partagée : `openai_compat.py`.
- `grok` : XAI_API_KEY, https://api.x.ai/v1, GROK_MODEL=grok-4.5
- `v100` : V100_BASE_URL=http://127.0.0.1:8000/v1, V100_MODEL
