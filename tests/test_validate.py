from rigor.model import Namespace, Validator, State


JSON_DICT = {
    "args": {},
    "headers": {
        "Accept": "*/*",
        "Connection": "close",
        "Host": "httpbin.org",
        "User-Agent": "curl/7.51.0"
    },
    "origin": "127.0.0.1",
    "url": "https://httpbin.org/get"
}

VALIDATION_STRING = [
    'response.url == "https://httpbin.org/get"',
    'response.args == {}',
    'response.origin is not None',
    'response["headers.Accept"] == "*/*"',
    'response["headers.Connection"] == "close"'
]


def test_jmespath_access():
    response = Namespace(JSON_DICT)
    assert response['url'] == "https://httpbin.org/get"
    assert response.args == {}
    assert response["headers.Accept"] == "*/*"
    assert response.origin is not None
    assert response["headers.Connection"] == "close"


def test_mako_templates():
    response = Namespace(JSON_DICT)
    state = State(response=response)

    for validation_string in VALIDATION_STRING:
        validator = Validator(validation_string)
        assert validator.is_valid(state)
