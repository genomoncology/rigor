from rigor import Suite, Config, Namespace, Validator, State, ReportEngine,\
    execute

from collections import OrderedDict

import pytest
import os

ROOT_DIR = os.path.join(os.path.dirname(__file__), "httpbin")
paths = [ROOT_DIR]


@pytest.fixture
def config():
    return Config.load(paths)


@pytest.fixture
def suite(config):
    return Suite.create(paths, config, excludes=["broken", "profile-only"])


@pytest.fixture
def sync_suite(config):
    return Suite.create(paths, config, excludes=["broken", "profile-only"],
                        concurrency=0)


def test_collect(suite):
    assert suite.excludes == ["broken", "profile-only"]
    assert len(suite.skipped) == 5
    assert len(suite.queued) == 10
    assert suite.name == "__root__"


def test_execute(suite):
    result = execute(suite)
    assert result.success, "Failed: %s" % result.failed
    assert len(result.passed) == 10

    engine = ReportEngine(suite_result=result, with_html=True)
    report_path = engine.generate()
    assert os.path.exists(report_path)


def test_execute_sync(sync_suite):
    result = execute(sync_suite)
    assert result.success, "Failed: %s" % result.failed
    assert len(result.passed) == 10


def test_case_get(suite):
    case = suite.get_case(ROOT_DIR, "get.rigor")

    # check case root
    assert case.name == "Get"
    assert case.format == "1.0"
    assert case.host == "https://httpbin.org"
    assert case.tags == ["working"]
    assert len(case.steps) == 2

    # check case steps
    step = case.steps[0]
    assert step.description == "Get call with no parameters"
    assert step.request.path == "get"
    assert step.validate == [
        Validator(actual="{response.url}", expect="https://httpbin.org/get"),
        Validator(actual="{response.args}", expect=OrderedDict()),
        Validator(actual="{response.headers.Accept}", expect="*/*"),
        Validator(actual="{response.headers.Connection}", expect="close"),
        Validator(actual="{response.headers.Authorization}",
                  expect="Token GUEST-TOKEN"),
    ]


def test_case_params(suite):
    case = suite.get_case(ROOT_DIR, "params.rigor")

    # check case root
    assert case.name == "Params"
    assert case.format == "1.0"
    assert case.host == "https://httpbin.org"
    assert case.tags == ["working"]
    assert len(case.steps) == 1
    assert len(case.scenarios) == 3

    # check scenarios
    assert case.scenarios[0] == Namespace(value=1, __name__="Scenario #1")
    assert case.scenarios[1] == Namespace(value=2, __name__="Override!")
    assert case.scenarios[2] == Namespace(value=['a', 'b', 'c'],
                                          __name__="Scenario #3")


def test_case_http_status(suite):
    case = suite.get_case(ROOT_DIR, "http_status.rigor")

    # check case root
    assert case.name == "HTTP Status"
    assert case.format == "1.0"
    assert case.host == "https://httpbin.org"
    assert len(case.steps) == 4
    assert len(case.scenarios) == 1  # default empty scenario

    # check step
    assert case.steps[0].request.status == []
    assert case.steps[1].request.status == [200]
    assert case.steps[2].request.status == [404]
    assert case.steps[3].request.status == [418]


def test_case_iterate(suite):
    case = suite.get_case(ROOT_DIR, "iterate.rigor")
    assert len(case.steps) == 4
    step = case.steps[0]
    namespace = State(case=case).namespace

    assert list(step.iterate.iterate(namespace)) == [
        dict(show_env=0, other="A"),
        dict(show_env=1, other="B"),
    ]
    step = case.steps[2]
    assert list(step.iterate.iterate(namespace)) == [
        dict(show_env=0, other="A"),
        dict(show_env=0, other="B"),
        dict(show_env=0, other="C"),
        dict(show_env=0, other="D"),
        dict(show_env=0, other="E"),
        dict(show_env=0, other="F"),
        dict(show_env=1, other="A"),
        dict(show_env=1, other="B"),
        dict(show_env=1, other="C"),
        dict(show_env=1, other="D"),
        dict(show_env=1, other="E"),
        dict(show_env=1, other="F"),
    ]


def test_case_load_yaml(suite):
    case = suite.get_case(ROOT_DIR, "load_yaml.rigor")
    assert len(case.scenarios) == 2
    assert len(case.steps) == 1

    scenario = case.scenarios[0]
    assert scenario.keys() == {"data", "__name__"}
    assert scenario['__name__'] == "same"

    scenario = case.scenarios[1]
    assert scenario.keys() == {"data", "__name__"}
    assert scenario['__name__'] == "same"


def test_case_conditional(config):
    paths = [os.path.join(ROOT_DIR, "conditional.rigor")]
    suite = Suite.create(paths, config)
    assert len(suite.skipped) == 0
    assert len(suite.queued) == 1
    result = execute(suite)
    assert not result.success  # test fails, checking # of steps
    assert len(result.failed) == 1
    scenario_result = result.failed[0].failed[0]
    assert len(scenario_result.step_results) == 2


def test_profile_only(config):
    profile = config.get_profile("www")
    suite = Suite.create(paths, profile)

    assert len(suite.queued) == 1
    assert len(suite.skipped) == 14
    assert suite.name == "www"

    result = execute(suite)
    assert result.success
