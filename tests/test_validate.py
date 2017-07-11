from rigor import Runner, Namespace, Validator


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

VALIDATION_KWARGS = [
    dict(expect="${response.url}", actual="https://httpbin.org/get"),
    # dict(expect="${response.args}", actual={}),
    dict(expect="${response.origin}", actual="127.0.0.1"),
    dict(expect="${response['headers.Accept']}", actual="*/*"),
    dict(expect="${response['headers.Connection']}", actual="close"),
    # dict(expect="${response.headers}", actual=JSON_DICT['headers']),
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
    runner = Runner(response=response)

    for kwargs in VALIDATION_KWARGS:
        validator = Validator(**kwargs)
        result = runner.check_validation(validator)
        assert result.success, "%s != %s" % (result.expect, result.actual)
