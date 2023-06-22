import pytest

from unicore.utils.lazy import lazyproperty


class MyClass:
    @lazyproperty
    def lazy(self):
        print("performing computation")
        return "computed value"


def test_shadow_cache(capfd: pytest.CaptureFixture):
    obj = MyClass()

    # Test that value is computed and cached
    with pytest.raises(AttributeError):
        obj.lazy_attr
    out, err = capfd.readouterr()
    assert obj.lazy == "computed value"
    out, err = capfd.readouterr()
    assert "performing computation" in out

    # Should not print
    assert obj.lazy == "computed value"
    out, err = capfd.readouterr()
    assert not out

    # Test that cache is invalidated
    del obj.lazy

    assert obj.lazy == "computed value"
    out, err = capfd.readouterr()
    assert "performing computation" in out
    assert obj.lazy == "computed value"
    out, err = capfd.readouterr()
    assert not out

    # Test that attribute can't be set directly
    with pytest.raises(AttributeError, match="does not support assignment"):
        obj.lazy = "new value"


if __name__ == "__main__":
    pytest.main([__file__])
