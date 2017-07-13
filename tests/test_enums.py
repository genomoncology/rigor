from rigor import Comparison


def test_equals():
    assert Comparison.EQUALS.evaluate(1, 1)
    assert Comparison.EQUALS.evaluate('hi', 'hi')
    assert not Comparison.EQUALS.evaluate('1', 1)
    assert not Comparison.EQUALS.evaluate('1', None)


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
