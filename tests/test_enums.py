from rigor import Comparison

# equality


def test_equals():
    assert Comparison.EQUALS.evaluate(1, 1)
    assert Comparison.EQUALS.evaluate(None, None)
    assert Comparison.EQUALS.evaluate('hi', 'hi')
    assert not Comparison.EQUALS.evaluate('1', 1)
    assert not Comparison.EQUALS.evaluate('1', None)


def test_not_equals():
    assert not Comparison.NOT_EQUALS.evaluate(1, 1)
    assert not Comparison.NOT_EQUALS.evaluate(None, None)
    assert not Comparison.NOT_EQUALS.evaluate('hi', 'hi')
    assert Comparison.NOT_EQUALS.evaluate('1', 1)
    assert Comparison.NOT_EQUALS.evaluate('1', None)


def test_same():
    assert Comparison.SAME.evaluate((1, 3), (1, 3))
    assert Comparison.SAME.evaluate((3, 1), (1, 3))
    assert Comparison.SAME.evaluate((1, 3), (3, 1))
    assert Comparison.SAME.evaluate(1, 1)
    assert Comparison.SAME.evaluate(None, None)
    assert Comparison.SAME.evaluate('hi', 'hi')
    assert not Comparison.SAME.evaluate('1', 1)
    assert not Comparison.SAME.evaluate('1', None)


def test_contains():
    assert Comparison.CONTAINS.evaluate(range(3), 1)
    assert Comparison.CONTAINS.evaluate(('hi',), 'hi')
    assert not Comparison.CONTAINS.evaluate(range(3), '1')
    assert not Comparison.CONTAINS.evaluate(None, '1')
    assert not Comparison.CONTAINS.evaluate(None, None)


def test_not_contains():
    assert not Comparison.NOT_CONTAINS.evaluate(range(3), 1)
    assert not Comparison.NOT_CONTAINS.evaluate(('hi',), 'hi')
    assert Comparison.NOT_CONTAINS.evaluate(range(3), '1')
    assert not Comparison.NOT_CONTAINS.evaluate(None, '1')
    assert not Comparison.NOT_CONTAINS.evaluate(None, None)


def test_in():
    assert Comparison.IN.evaluate(1, range(3))
    assert Comparison.IN.evaluate('hi', ('hi',))
    assert not Comparison.IN.evaluate('1', range(3))
    assert not Comparison.IN.evaluate('1', None)
    assert not Comparison.IN.evaluate(None, None)


def test_not_in():
    assert not Comparison.NOT_IN.evaluate(1, range(3))
    assert not Comparison.NOT_IN.evaluate('hi', ('hi',))
    assert Comparison.NOT_IN.evaluate('1', range(3))
    assert not Comparison.NOT_IN.evaluate('1', None)
    assert not Comparison.NOT_IN.evaluate(None, None)


def test_greater_than():
    assert Comparison.GREATER_THAN.evaluate(1, 0)
    assert not Comparison.GREATER_THAN.evaluate(0, 0)
    assert not Comparison.GREATER_THAN.evaluate(0, 1)

    assert Comparison.GT.evaluate(1, 0)
    assert not Comparison.GT.evaluate(0, 0)
    assert not Comparison.GT.evaluate(0, 1)
    assert not Comparison.GT.evaluate(0, None)
    assert not Comparison.GT.evaluate(None, 0)
    assert not Comparison.GT.evaluate("1", 0)
    assert not Comparison.GT.evaluate(1, "0")
    assert not Comparison.GT.evaluate(0, "1")


def test_greater_than_or_equals():
    assert Comparison.GREATER_THAN_OR_EQUALS.evaluate(1, 1)
    assert Comparison.GREATER_THAN_OR_EQUALS.evaluate(2, 1)
    assert Comparison.GREATER_THAN_OR_EQUALS.evaluate(1, -1)
    assert not Comparison.GREATER_THAN_OR_EQUALS.evaluate(1, 3)

    assert Comparison.GTE.evaluate(1, 1)
    assert Comparison.GTE.evaluate(2, 1)
    assert Comparison.GTE.evaluate(1, -1)
    assert not Comparison.GTE.evaluate(1, 3)


def test_less_than_or_equals():
    assert Comparison.LESS_THAN_OR_EQUALS.evaluate(1, 1)
    assert Comparison.LESS_THAN_OR_EQUALS.evaluate(1, 2)
    assert Comparison.LESS_THAN_OR_EQUALS.evaluate(-1, 1)
    assert not Comparison.LESS_THAN_OR_EQUALS.evaluate(3, 1)

    assert Comparison.LTE.evaluate(1, 1)
    assert Comparison.LTE.evaluate(1, 2)
    assert Comparison.LTE.evaluate(-1, 1)
    assert not Comparison.LTE.evaluate(3, 1)


def test_type():
    assert Comparison.TYPE.evaluate(1, "int")
    assert Comparison.TYPE.evaluate(2.0, "float")
    assert Comparison.TYPE.evaluate("hello", "str")
    assert Comparison.TYPE.evaluate([1, 2], "list")
    assert Comparison.TYPE.evaluate(dict(a=1), "dict")


def test_regex():
    assert Comparison.REGEX.evaluate("", ".*")
    assert Comparison.REGEX.evaluate("2222", "\d+")
    assert Comparison.REGEX.evaluate("111-33-3333", "\d{3}-\d{2}-\d{4}")
    assert Comparison.REGEX.evaluate("John Q. Public", "\w+ \w\. \w+")
