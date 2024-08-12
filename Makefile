update:
	uv pip compile pyproject.toml --output-file requirements.txt


#----------
# test
#----------

test:
	pytest


run:
	rigor tests/httpbin/ --excludes=broken

rebuild:
	cd ~/code/rigor; \
	python3 -m pip install --upgrade build; \
	python3 -m build


