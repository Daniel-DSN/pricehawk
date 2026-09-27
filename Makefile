.PHONY: install test demo scrape diff clean

install:
	pip install -r requirements.txt

test:
	PYTHONPATH=src python3 -m pytest -q

demo: scrape
	@echo "--- second run to build history ---"
	python -m pricehawk.cli scrape "http://books.toscrape.com/" -o products2.csv --history history.json --pages 2
	python -m pricehawk.cli diff --history history.json

scrape:
	PYTHONPATH=src python -m pricehawk.cli scrape "http://books.toscrape.com/" \
		-o products.csv --history history.json --pages 2

diff:
	PYTHONPATH=src python -m pricehawk.cli diff --history history.json

clean:
	rm -f products*.csv products*.xlsx history.json
	find . -name __pycache__ -type d -exec rm -rf {} +
