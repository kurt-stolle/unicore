.PHONY: build, benchmark, clean, coverage, dist

build:
	python -m build

dist: build
	python -m twine upload dist/*

clean:
	rm -rf build/ dist/ *.egg-info/

test:
	python -m pytest -s -v -n auto --dist=loadfile --junitxml=tests.xml --no-cov --benchmark-disable

benchmark:
	python -m pytest -s -v -n 0 --no-cov benchmarks

coverage:
	python -m pytest --cov=sources --cov-report=html --cov-report=xml --benchmark-disable
