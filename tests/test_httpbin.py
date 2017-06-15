from rigor.model import Suite, Method

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
    assert len(suite.active) == 2


def test_basic(suite):
    case = suite.get_active_case(ROOT_DIR, "basic.yml")

    # check case root
    assert case.name == "Basic Get"
    assert case.format == "1.0"
    assert case.domain == "https://httpbin.org"
    assert case.tags == ["working"]
    assert len(case.steps) == 1

    # check case steps
    step = case.steps[0]
    assert step.description == "Get call with no parameters"
    assert step.request.url == "/get"
    assert step.validate == [
        'response.url == "https://httpbin.org/get"',
        'response.args == {}',
        'response.headers.Accept == "*/*"',
        'response.origin is not None',
        'response.headers.Connection == "close"',
    ]


def test_show_env(suite):
    case = suite.get_active_case(ROOT_DIR, "show_env.yml")

    # check case root
    assert case.name == "Show Environment Get"
    assert case.format == "1.0"
    assert case.domain == "https://httpbin.org"
    assert case.tags == ["working"]
    assert len(case.steps) == 1

    # check case steps
    step = case.steps[0]
    assert step.description == "Pass the show_env=1 flag to the get end-point."
    assert step.request.url == "/get?show_env=1"
    assert step.validate == [
        'response.url == "https://httpbin.org/get?show_env=1"',
        'response.args.show_env = "1"',
        'response.headers.Accept == "*/*"',
        'response.headers.Connection == "close"',
        'response.headers["X-Forwarded-Proto"] == "https"',
    ]
