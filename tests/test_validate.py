from rigor import State, Namespace, Validator


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
    dict(expect="{response.url}", actual="https://httpbin.org/get"),
    dict(expect="{response.origin}", actual="127.0.0.1"),
    dict(expect="{response.headers.Accept}", actual="*/*"),
    dict(expect="{response.headers.Connection}", actual="close"),
]


def test_namespace_access():
    response = Namespace(JSON_DICT)
    assert Namespace.render("{url}", response) == "https://httpbin.org/get"
    assert Namespace.render("{args}", response) == {}
    assert Namespace.render("{headers.Accept}", response) == "*/*"
    assert Namespace.render("{origin}", response) is not None
    assert Namespace.render("{headers.Connection}", response) == "close"


def test_fstring_templates():
    response = Namespace(JSON_DICT)
    runner = State(response=response)

    for kwargs in VALIDATION_KWARGS:
        validator = Validator(**kwargs)
        result = runner.check_validation(validator)
        assert result.success, "%s != %s" % (result.expect, result.actual)
