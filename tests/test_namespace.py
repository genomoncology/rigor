from rigor import Namespace


def test_namespace_render():
    assert Namespace.render("000-00-0000", {}) == "000-00-0000"
    assert Namespace.render("22", {}) == 22
    assert Namespace.render("-22.330", {}) == -22.330
    assert Namespace.render_string("['1', '2', '3']", {}) == ["1", "2", "3"]
    assert Namespace.render_string("range(2,12)", {}) == [
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
    ]
    assert Namespace.render_string("range(3)", {}) == [0, 1, 2]
    assert Namespace.render_string("range_inclusive(2,12)", {}) == [
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
    ]
    assert Namespace.render_string("range_inclusive(3)", {}) == [0, 1, 2, 3]

    # test range with variable name(s)
    assert Namespace.render_string("range($val)", {"val": 3}) == [0, 1, 2]
    assert Namespace.render_string(
        "range($val1, $val2)", {"val1": 3, "val2": 5}
    ) == [3, 4]


def test_unknown_variables():
    assert Namespace.render_string("{{ $unknown }}", {}) == "{ $unknown }"
    assert Namespace.render_string("{ $unknown }", {}) == "{ $unknown }"
    assert Namespace.render_string("{ unknown }", {}) == "{ unknown }"
    assert Namespace.render_string("{{ unknown }}", {}) == "{ unknown }"


def test_hasattr():
    ns = Namespace(dict(a=1))
    assert hasattr(ns, "a")
    assert not hasattr(ns, "b")
