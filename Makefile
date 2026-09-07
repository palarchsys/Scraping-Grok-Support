.PHONY: install test scrape analyze run stats triage db db-init scrape-live probe

install:
	./install.sh

db:
	./scripts/init-db.sh

db-init:
	.venv/bin/scraping-grok db-init

test:
	.venv/bin/pytest -q

scrape:
	.venv/bin/scraping-grok scrape

scrape-live:
	.venv/bin/scraping-grok scrape --live

analyze:
	.venv/bin/scraping-grok analyze

run:
	.venv/bin/scraping-grok run

triage:
	.venv/bin/scraping-grok triage

stats:
	.venv/bin/scraping-grok stats

probe:
	.venv/bin/scraping-grok probe --source francetvinfo_faits_divers

