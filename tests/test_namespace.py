from rigor import Namespace


def test_namespace_render():
    assert Namespace.render("000-00-0000", {}) == "000-00-0000"
