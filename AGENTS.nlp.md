# Étape 2 NLP — contrat court

Entrée : articles `statut=ok` non analysés. Sortie : `incidents` + `articles.analyzed_at`.

## Taxonomie (fermée)
violence_physique | agression_sexuelle | homicide | tentative | menace | vol_avec_violence | autre_agression | non_agression

## Flux
`prefilter → si miss: skip non_agression → connector.complete_json → IncidentExtraction.model_validate → si non_agression ou confidence<seuil: identifiants NULL → store`

LLM parallèle (`NLP_CONCURRENCY`, défaut 4). Writes SQLite en série.

## Connecteurs
Interface `LlmConnector.complete_json(system, user) -> dict`.
Implémentation partagée : `openai_compat.py`.
- `grok` : XAI_API_KEY, https://api.x.ai/v1, GROK_MODEL=grok-4.5
- `v100` : V100_BASE_URL=http://127.0.0.1:8000/v1, V100_MODEL

Ne pas dupliquer le prompt. Ne pas appeler le LLM pendant le scrape.

## Extraction
Champs auteur/date : NULL si non explicites. Jamais d’inférence ethnique. Preuves = citations courtes.

## V100 32 Go
vLLM `Qwen/Qwen2.5-14B-Instruct-AWQ` ou llama.cpp Qwen2.5-14B Q4_K_M. Contexte 4k. Batch 1–8. `scripts/serve-v100.sh`
