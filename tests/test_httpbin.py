from rigor.model import Suite, Method, Namespace, Validator, State
from collections import OrderedDict

import pytest
import os
import related
import json

ROOT_DIR = os.path.join(os.path.dirname(__file__), "httpbin")


@pytest.fixture
def suite():
    directories = [ROOT_DIR]
    return Suite(directories=directories, tags_excluded=["broken"])


def test_collect(suite):
    assert suite.tags_excluded == ["broken"]
    assert len(suite.skipped) == 2
    assert len(suite.queued) == 6
    assert len(suite.failed) == 0
    assert len(suite.passed) == 0


def test_execute(suite):
    success = suite.execute()
    assert success
    assert len(suite.passed) == 6


def test_case_get(suite):
    case = suite.get_case(ROOT_DIR, "get.rigor")

    # check case root
    assert case.name == "Get"
    assert case.format == "1.0"
    assert case.domain == "https://httpbin.org"
    assert case.tags == ["working"]
    assert len(case.steps) == 1

    # check case steps
    step = case.steps[0]
    assert step.description == "Get call with no parameters"
    assert step.request.path == "/get"
    assert step.validate == [
        Validator(expect="${response.url}", actual="https://httpbin.org/get"),
        Validator(expect="${response.args}", actual=OrderedDict()),
        Validator(expect="${response['headers.Accept']}", actual="*/*"),
        Validator(expect="${response['headers.Connection']}", actual="close"),
    ]


def test_case_params(suite):
    case = suite.get_case(ROOT_DIR, "params.rigor")

    # check case root
    assert case.name == "Params"
    assert case.format == "1.0"
    assert case.domain == "https://httpbin.org"
    assert case.tags == ["working"]
    assert len(case.steps) == 2
    assert len(case.scenarios) == 1

    # check scenarios
    assert case.scenarios[0] == Namespace(start=1, adder=2, check=3, final=5)

    # check last step
    step = case.steps[-1]
    assert step.description == "Pass the show_env flag from previous case."
    assert step.request.path == "/get"
    assert step.request.params == dict(show_env="${extract.check}")

    assert step.extract == Namespace(
        final='${response["args.show_env"]} + ${scenario.adder}'
    )

    assert step.validate == [
        Validator(expect='https://httpbin.org/get?show_env=${extract.check}',
                  actual='${response.url}'),
        Validator(expect='${extract.check}',
                  actual="${response['args.show_env']}"),
        Validator(expect='${scenario.final}', actual='${final}'),
        Validator(expect='${scenario.final}', actual='${extract.final}')]


def test_case_http_status(suite):
    case = suite.get_case(ROOT_DIR, "http_status.rigor")

    # check case root
    assert case.name == "HTTP Status"
    assert case.format == "1.0"
    assert case.domain == "https://httpbin.org"
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
    state = State(case=case)

    assert list(step.iterate.iterate(state)) == [
        dict(show_env=0, other="A"),
        dict(show_env=1, other="B"),
    ]
    step = case.steps[2]
    assert list(step.iterate.iterate(state)) == [
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


def test_case_iyaml(suite):
    case = suite.get_case(ROOT_DIR, "list_yaml.rigor")
    assert len(case.steps) == 1
    step = case.steps[0]
    assert step.iterate == dict(data="${list_yaml('./data/example.yaml')}")

    state = State(case=case)
    iterate = list(step.iterate.iterate(state))

    iter0 = iterate[0]
    assert isinstance(iter0, dict)
    assert iter0['data']['request']['query'] == "field:val"
