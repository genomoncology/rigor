from rigor.model import Suite, Method, Namespace, Validator
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
    assert len(suite.skipped) == 3
    assert len(suite.queued) == 2
    assert len(suite.failed) == 0
    assert len(suite.passed) == 0


def test_collect_basic(suite):
    case = suite.get_case(ROOT_DIR, "basic.yml")

    # check case root
    assert case.name == "Basic Get"
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


def test_collect_show_env(suite):
    case = suite.get_case(ROOT_DIR, "show_env.yml")

    # check case root
    assert case.name == "Show Environment Get"
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


def test_execute(suite):
    success = suite.execute()
    assert success
    assert len(suite.passed) == 2
