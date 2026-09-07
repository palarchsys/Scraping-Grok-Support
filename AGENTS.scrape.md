# Étape 1 scrape — Scrapy + PostgreSQL

Live : skip GET si URL déjà en `articles` (y compris ignored). Stop pagination si page sans URL neuve ou XPath vide.

Probe : `scraping-grok probe --source ID [--save]`. Si `playwright_suggere`, le HTML est un mur cookies/JS — ne pas ajouter Playwright par défaut.
