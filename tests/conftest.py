import rigor


def pytest_runtest_setup(item):
    rigor.setup_logging(quiet=False, json=False)
