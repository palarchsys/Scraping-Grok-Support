.PHONY: install test scrape analyze run stats triage db db-init scrape-live

install:
	./install.sh

db:
	./scripts/init-db.sh

db-init:
	.venv/bin/sscraping db-init

test:
	.venv/bin/pytest -q

scrape:
	.venv/bin/sscraping scrape

scrape-live:
	.venv/bin/sscraping scrape --live

analyze:
	.venv/bin/sscraping analyze

run:
	.venv/bin/sscraping run

triage:
	.venv/bin/sscraping triage

stats:
	.venv/bin/sscraping stats
