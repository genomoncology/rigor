import pytest
import rigor


@pytest.fixture(scope="module")
def pytest_runtest_setup(item):
    rigor.setup_logging(quiet=True, json=True)
