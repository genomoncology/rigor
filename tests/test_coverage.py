from rigor import Config, Suite, SuiteResult
import pytest
import os.path


CONFIG_DIR = os.path.join(os.path.dirname(__file__), "coverage")
HOST = "https://raw.githubusercontent.com/OAI/OpenAPI-Specification"
SCHEMA = "/master/examples/v2.0/json/petstore-simple.json"


@pytest.fixture
def config():
    return Config.load([CONFIG_DIR])


@pytest.fixture
def suite(config):
    return Suite.create(['.'], config)


@pytest.fixture
def result(suite):
    return SuiteResult(suite=suite)


def test_config_ok_in_suite(suite):
    assert suite.host == HOST
    assert suite.schemas['v2-simple'] == SCHEMA


def test_suite_result(suite, result):
    assert result.suite == suite
