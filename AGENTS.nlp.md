# Étape 2 NLP — Grok only

Entrée : `analyze_status=pending` uniquement. `ignored` / `extracted` / `error` = déjà traité, jamais renvoyé.

préfiltre → compressé ≤1800c → JSON (1 retry) → preuves locales → `incidents` + `faits`.

`auteurs[]` = mis en cause (interpellé / mis en examen), pas la victime. `lieu` = ville.

Groupage : nom+prénom+date±1j+lieu, sinon similarité de titre.

Tokens : logs `prompt_tokens` / `completion_tokens` / `calls`.
