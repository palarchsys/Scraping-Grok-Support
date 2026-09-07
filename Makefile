.PHONY: install v100 test scrape analyze run stats db db-init scrape-live

install:
	./install.sh

v100:
	./install.sh --v100

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
	.venv/bin/sscraping analyze --backend grok

run:
	.venv/bin/sscraping run --backend grok

stats:
	.venv/bin/sscraping stats
