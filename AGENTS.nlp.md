# Étape 2 NLP — Grok only

Entrée : articles non analysés. Sortie : `incidents` + `faits` + `analyzed_at`.

## Tokens
préfiltre (1 fort ou 2 faibles) → `compress_for_llm` lead+phrases clés ≤1800c → SYSTEM_PROMPT statique → max_tokens 280 → `local_preuves` (pas le LLM).

## 8 groupes
atteintes_vie | violences_personnes | atteintes_sexuelles | atteintes_biens | stupefiants | criminalite_economique | circulation_securite | ordre_public_surete

## Groupage
`grouping_key` = norm(nom)+norm(prénom)+année+mois+jour. Incomplet → pas de `fait_id`.

Connecteur : `GrokConnector` uniquement (`XAI_API_KEY`, `grok-4.5`).
