from rigor import Config, Suite, Swagger, execute, CoverageReport
import pytest
import os.path
import os


CONFIG_DIR = os.path.join(os.path.dirname(__file__), "petstore")
HOST = "https://raw.githubusercontent.com"
SCHEMA = "OAI/OpenAPI-Specification/master/examples/v2.0/" \
         "json/petstore-simple.json"


@pytest.fixture
def config():
    return Config.load([CONFIG_DIR])


@pytest.fixture
def suite(config):
    return Suite.create([CONFIG_DIR], config)


@pytest.fixture
def schema(suite):
    schemas = Swagger.gather_schemas(suite)
    assert len(schemas) == 1
    return schemas[0]


@pytest.fixture
def result(suite):
    return execute(suite)


@pytest.fixture
def report(result):
    return CoverageReport.create(result)


def test_config_ok_in_suite(suite):
    assert suite.host == HOST
    assert suite.schemas['v2-simple'] == SCHEMA
    assert len(suite.queued) == 2


def test_schema_ok(schema):
    assert len(schema.paths) == 2


def test_suite_result(result):
    assert len(result.passed) == 1

    case_result = result.passed[0]
    assert case_result.case.name == "Example tests that will return 4xx"


def test_report_for_detail(report):
    path_report = report.get_method_report("/pets/1", "get")
    assert path_report.url == "/pets/{id}"
    assert path_report.case_counts.passed == 1
    assert path_report.case_counts.failed == 1
    assert path_report.scenario_counts.passed == 1
    assert path_report.scenario_counts.failed == 1
    assert path_report.step_counts.passed == 1
    assert path_report.step_counts.failed == 1
    assert len(path_report.counts) == 4

    output_path = report.generate(None)
    assert "coverage" in output_path
    assert output_path.endswith(".xls")
