import pytest

from unicore.catalog import fork


@pytest.fixture
def catalog():
    return fork()


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
    @catalog.register_info("foo_data")
    def _():
        return {"test_info": "bar"}

    info = catalog.get_info("foo_data")

    assert info["test_info"] == "bar"

    with pytest.raises(KeyError):
        catalog.get_info("bar_data")
        nonexists = info["test_value"]
        assert nonexists is None
