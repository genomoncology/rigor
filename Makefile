#----------
# test
#----------

test:
	pipenv run python setup.py test

test-all: clean
	tox

run:
	rigor tests/httpbin/ --excludes=broken

#----------
# clean
#----------

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

#----------
# publish
#----------

pex:
	pip wheel . -w ./build/mac-wheels
	pex --python=python3.6 -f ./build/mac-wheels rigor -e rigor.cli:main -o ./build/rigor -v --disable-cache


publish:
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload dist/*
	rm -fr build dist .egg related.egg-info
