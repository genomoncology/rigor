from rigor import Config, Namespace, Suite

import pytest
import os

DIR_NAME = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(DIR_NAME, "config")
GLOBAL_SCORE = 20
TEST_ADMIN_TOKEN = "a333333333333333333333333333333333333333"
OAUTH_TOKEN = "a333333333333333333333333333333333333333"

os.environ['RIGOR_GLOBAL_SCORE'] = str(GLOBAL_SCORE)
os.environ['RIGOR_TEST_ADMIN_TOKEN'] = TEST_ADMIN_TOKEN
os.environ['RIGOR_OAUTH_TOKEN'] = OAUTH_TOKEN


@pytest.fixture
def root():
    return Config.load([CONFIG_DIR])


@pytest.fixture
def local(root):
    return root.get_profile('local')


@pytest.fixture
def test(root):
    return root.profiles['test']


@pytest.fixture
def production(root):
    return root.profiles['production']


def test_root_profile(root):
    assert root.name == "__root__"
    assert root.file_path == os.path.join(CONFIG_DIR, "rigor.yml")
    assert root.host == "http://localhost:8000"

    # sanity check
    assert len(root.schemas) == 2
    assert len(root.globals) == 4
    assert len(root.headers) == 2
    assert len(root.profiles) == 3

    # schemas
    assert root.schemas['v1'] == "/api/v1/schema?format=openapi"
    assert root.schemas['v2'] == "/api/v2/schema?format=openapi"

    # globals
    ns = root.globals
    assert Namespace.render("{language}", ns) == "Python"
    assert Namespace.render("{pi}", ns) == pytest.approx(3.14159)
    assert Namespace.render("{score}", ns) == GLOBAL_SCORE
    assert Namespace.render("{tokens.admin}", ns) == 'a' + '0' * 39
    assert Namespace.render("{tokens.staff}", ns) == 'a' + '1' * 39
    assert Namespace.render("{tokens.guest}", ns) == 'a' + '2' * 39
    assert Namespace.render("{tokens.oauth}", ns) == {}

    # headers
    assert root.headers.get("Authorization") == "Token {tokens.guest}"
    assert root.headers.get("Content-Type") == "application/json"

    # other
    assert root.extensions == ["rigor"]
    assert root.includes == []
    assert root.excludes == ["broken"]
    assert root.concurrency == 10


def test_local_profile(local):
    # host
    assert local.host == "http://localhost:8000"

    # schemas
    assert local.schemas['v1'] == "/api/v1/schema?format=openapi"
    assert local.schemas['v2'] == "/api/v2/schema?format=openapi"
    assert local.schemas['v3'] == "/api/v3/schema?format=openapi"
    assert local.schemas['v4'] == "/api/v4/schema?format=openapi"

    # globals
    ns = local.globals
    assert Namespace.render("{language}", ns) == "Python"
    assert Namespace.render("{pi}", ns) == pytest.approx(3.14159)
    assert Namespace.render("{score}", ns) == GLOBAL_SCORE
    assert Namespace.render("{tokens.admin}", ns) == 'a' + '0' * 39
    assert Namespace.render("{tokens.staff}", ns) == 'a' + '1' * 39
    assert Namespace.render("{tokens.guest}", ns) == 'a' + '2' * 39
    assert Namespace.render("{tokens.oauth}", ns) == {}

    # headers
    assert local.headers.get("Authorization") == "Token {tokens.guest}"
    assert local.headers.get("Content-Type") == "application/json"

    # other
    assert local.extensions == ["rigor"]
    assert local.includes == []
    assert local.excludes == ["broken"]
    assert local.concurrency == 10


def test_test_profile(test):
    # host
    assert test.host == "http://test.host.com"

    # schemas
    assert test.schemas['v1'] == "/api/v1/schema?format=openapi"
    assert test.schemas['v2'] == "/api/v2/schema?format=openapi"
    assert test.schemas['v3'] == "/api/v3/schema?format=openapi"
    assert test.schemas.get('v4') is None

    # globals
    ns = test.globals
    assert Namespace.render("{language}", ns) == "Python"
    assert Namespace.render("{pi}", ns) == pytest.approx(3.14159)
    assert Namespace.render("{score}", ns) == GLOBAL_SCORE
    assert Namespace.render("{tokens.admin}", ns) == TEST_ADMIN_TOKEN
    assert Namespace.render("{tokens.staff}", ns) == 'a' + '1' * 39
    assert Namespace.render("{tokens.guest}", ns) == 'a' + '2' * 39
    assert Namespace.render("{tokens.oauth}", ns) == OAUTH_TOKEN

    # headers
    assert test.headers.get("Authorization") == "Bearer {tokens.oauth}"
    assert test.headers.get("Content-Type") == "application/json"

    # other
    assert test.extensions == ["rigor"]
    assert test.includes == []
    assert test.excludes == ["broken"]
    assert test.concurrency == 10


def test_production_profile(production):
    # host
    assert production.host == "http://production.host.com"

    # schemas
    assert production.schemas['v1'] == "/api/v1/schema?format=openapi"
    assert production.schemas['v2'] == "/api/v2/schema?format=openapi"
    assert production.schemas.get('v3') is None
    assert production.schemas.get('v4') is None

    # globals
    ns = production.globals
    assert Namespace.render("{language}", ns) == "Python"
    assert Namespace.render("{pi}", ns) == pytest.approx(3.14159)
    assert Namespace.render("{score}", ns) == GLOBAL_SCORE
    assert Namespace.render("{tokens.admin}", ns) == 'None'
    assert Namespace.render("{tokens.staff}", ns) == 'None'
    assert Namespace.render("{tokens.guest}", ns) == 'None'
    assert Namespace.render("{tokens.oauth}", ns) == 'None'

    # headers
    assert production.headers.get("Authorization") is None
    assert production.headers.get("Content-Type") == "application/json"

    # other
    assert production.extensions == ["rigor"]
    assert production.includes == []
    assert production.excludes == ["broken"]
    assert production.concurrency == 10


def test_suite_create(root):
    paths = ["."]
    suite = Suite.create(paths, root, extensions=(), excludes=(), includes=(),
                         concurrency=None)

    assert suite.extensions == ["rigor"]
    assert suite.includes == []
    assert suite.excludes == ["broken"]
    assert suite.concurrency == 10


def test_find_file():
    # navigates up to find dir tree the config file
    httpbin_data = os.path.join(DIR_NAME, "httpbin/data")
    httpbin_config = os.path.join(DIR_NAME, "httpbin/rigor.yml")
    config = Config.load([httpbin_data])
    assert config.file_path == httpbin_config


def test_missing_file():
    config = Config.load([DIR_NAME])
    assert config.file_path is None
