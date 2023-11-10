import pytest

from unicore.catalog import fork


@pytest.fixture
def catalog():
    return fork()


def test_canonicalize_id():
    from unicore.catalog import canonicalize_id

    assert canonicalize_id("foo") == "foo"
    assert canonicalize_id("Foo") == "foo"
    assert canonicalize_id("FooBar") == "foo-bar"
    assert canonicalize_id("FooBar/Baz") == "foo-bar/baz"
    assert canonicalize_id("foo_bar") == "foo-bar"
    assert canonicalize_id("foo_bar_baz") == "foo-bar-baz"
    assert canonicalize_id("foo-bar") == "foo-bar"
    assert canonicalize_id("foo-bar-baz") == "foo-bar-baz"
    assert canonicalize_id("foo-bar_baz") == "foo-bar-baz"
    assert canonicalize_id("foo_bar/baz") == "foo-bar/baz"
    assert canonicalize_id("foo/360") == "foo/360"
    assert canonicalize_id("foo/360-bar") == "foo/360-bar"


def test_catalog_register(catalog):
    @catalog.register_dataset()
    class FooData:
        test_value = "foo"

        @staticmethod
        def info():
            return {"test_info": "bar"}

    assert catalog.get_dataset("foo_data").test_value == "foo"

    with pytest.raises(KeyError):
        catalog.register_dataset("foo_data")(FooData)


def test_catalog_info(catalog):
    @catalog.register_info("foo-data")
    def _():
        return {"test_info": "bar"}

    info = catalog.get_info("foo-data")

    assert info["test_info"] == "bar"

    with pytest.raises(KeyError):
        catalog.get_info("bar_data")
        nonexists = info["test_value"]
        assert nonexists is None
