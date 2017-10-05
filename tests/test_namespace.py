from rigor import Namespace


def test_namespace_render():
    assert Namespace.render("000-00-0000", {}) == "000-00-0000"
    assert Namespace.render("22", {}) == 22
    assert Namespace.render("-22.330", {}) == -22.330
    assert Namespace.render_string("['1', '2', '3']", {}) == ['1', '2', '3']


def test_unknown_variables():
    assert Namespace.render_string("{{ $unknown }}", {}) == "{ $unknown }"
    assert Namespace.render_string("{ $unknown }", {}) == "{ $unknown }"
    assert Namespace.render_string("{ unknown }", {}) == "{ unknown }"
    assert Namespace.render_string("{{ unknown }}", {}) == "{ unknown }"


def test_hasattr():
    ns = Namespace(dict(a=1))
    assert hasattr(ns, "a")
    assert not hasattr(ns, "b")
