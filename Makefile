update:
	uv pip compile pyproject.toml --output-file requirements.txt


#----------
# test
#----------

test:
	pytest


run:
	rigor tests/httpbin/ --excludes=broken
