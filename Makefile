.PHONY: install v100 test scrape analyze run stats

install:
	./install.sh

v100:
	./install.sh --v100

test:
	.venv/bin/pytest -q

scrape:
	.venv/bin/sscraping scrape

analyze:
	.venv/bin/sscraping analyze --backend grok

run:
	.venv/bin/sscraping run --backend grok

stats:
	.venv/bin/sscraping stats
