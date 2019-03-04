from . import setup_logging, Case, Session, Suite, reporting

import pytest

setup_logging(quiet=True)
suite = Suite(host="http://localhost:8000", concurrency=0)
session = Session.create(suite)


def pytest_collect_file(parent, path):
    if path.strpath.endswith(".rigor"):
        reader = path.open()
        case = Case.loads(reader.read(), file_path=path.strpath)
        if case.is_active(suite.includes, suite.excludes):
            return PytestCase(path, parent, case)
    return None


class PytestCase(pytest.File):
    def __init__(self, fspath, parent, case):
        super().__init__(fspath, parent)
        self.case = case

    def collect(self):
        for scenario in self.case.scenarios:
            yield PytestScenario(self, self.case, scenario)


class PytestScenario(pytest.Item):
    def __init__(self, parent, case, scenario):
        super().__init__(scenario.__name__, parent)
        self.case = case
        self.scenario = scenario

    def runtest(self):
        self.result = session.run_case_scenario(self.case, self.scenario)
        assert self.result.success

    def repr_failure(self, excinfo):
        for step_result in self.result.step_results:
            if not step_result.success:
                return reporting.DocString.create(step_result).value

    def reportinfo(self):
        return self.fspath, 0, "%s [%s]" % (self.fspath, self.name)
