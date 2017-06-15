from rigor.model import Suite, Method

import pytest
import os
import related
import json


@pytest.fixture
def suite():
    return Suite.load(os.path.dirname(__file__))


@pytest.fixture
def case(suite):
    assert len(suite.cases) == 1
    return suite.cases[0]


def test_root(case):
    assert case.name == "Create Classifications"
    assert case.format == '1.0'
    assert len(case.steps) == 2


def test_headers(case):
    headers = case.headers
    auth = headers['Authorization']
    assert auth == 'Token 0000000000000000000000000000000000000000'


def test_step_0(case):
    step = case.steps[0]
    assert step.description == "Create data set for scenario."

    # request
    assert step.request.url == "/curation/data_sets/"
    assert step.request.method == Method.POST
    assert step.request.body == dict(name="${scenario.uuid}",
                                     full_name="${scenario.uuid}",
                                     default=False)

    # validate
    assert step.validate == ["scenario.uuid == response.name",
                             "scenario.uuid == response.full_name",
                             "False == response.default"]

    # extract
    assert step.extract == dict(data_set="${response.name}")


def test_step_1(case):
    step = case.steps[1]
    assert step.description == "Create classification."

    # request
    assert step.request.url == "/curation/classification/"
    assert step.request.method == Method.POST
    assert step.request.body == dict(data_set="${data_set}",
                                     hgvs_g="${scenario.hgvs_g}")

    # validate
    assert step.validate == ["scenario.title == response.title",
                             "data_set == response.data_set"]

    # extract
    assert step.extract == dict(classification_uuid="${response.uuid}")


def test_scenarios(case):
    assert case.scenarios == [
        dict(hgvs_g="NC_000007.13:g.140453136A>T",
             title="NM_004333.4(BRAF):c.1799T>A (p.Val600Glu)")
    ]
