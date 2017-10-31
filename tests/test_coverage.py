from rigor import Config, Suite, Swagger, execute
import pytest
import os.path


CONFIG_DIR = os.path.join(os.path.dirname(__file__), "petstore")
HOST = "https://raw.githubusercontent.com/OAI/OpenAPI-Specification"
SCHEMA = "master/examples/v2.0/json/petstore-simple.json"


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


def test_config_ok_in_suite(suite):
    assert suite.host == HOST
    assert suite.schemas['v2-simple'] == SCHEMA
    assert len(suite.queued) == 1


def test_schema_ok(schema):
    assert len(schema.paths) == 2


def test_suite_result(result):
    assert len(result.passed) == 1

    case_result = result.passed[0]
    assert case_result.case.name == "Example tests that will return 4xx"
