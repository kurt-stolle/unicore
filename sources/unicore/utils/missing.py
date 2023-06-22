from __future__ import annotations

import typing
from weakref import WeakValueDictionary

from typing_extensions import Self, override

_O = typing.TypeVar("_O", bound=typing.Any)
_O_co = typing.TypeVar("_O_co", bound=typing.Any, covariant=True)
_O_cn = typing.TypeVar("_O_cn", bound=typing.Any, contravariant=True)
_I = typing.TypeVar("_I", bound="type[MissingValue]")
_I_co = typing.TypeVar("_I_co", bound="type[MissingValue]", covariant=True)
_I_cn = typing.TypeVar("_I_cn", bound="type[MissingValue]", contravariant=True)


class MissingValue(typing.Generic[_O]):
    """A sentinel object that can be used as a value.

    Attributes
    ----------
    name : str
        The name of the sentinel value.

    """

    __sentinel_types__: typing.ClassVar[WeakValueDictionary[str, Self]] = WeakValueDictionary()

    def __new__(cls, name: str) -> Self:
        """
        Create a new sentinel value or return an existing one.

        Parameters
        ----------
        name : str
            The name of the sentinel value.

        Returns
        -------
        MissingValue
            The new or existing sentinel value.

        """
        name = name.upper()
        if name not in cls.__sentinel_types__:
            cls = super().__new__(cls)
            cls.__sentinel_types__[name] = cls
            # mcls.__sentinel_types__[name] = super().__new__(mcls, name, (), {})
        return cls.__sentinel_types__[name]

    def __init__(self, name: str) -> None:
        self.__name__: typing.Final[str] = name

    @override
    def __eq__(self, other: typing.Any) -> typing.TypeGuard[Self]:
        """
        Check if this sentinel value is equal to another object.

        Parameters
        ----------
        other : typing.Any
            The object to compare with this sentinel value.

        Returns
        -------
        bool
            True if the other object is a sentinel value with the same name,
            False otherwise.

        """
        return isinstance(other, MissingValue) and self.__name__ == other.__name__

    @override
    def __ne__(self, other: typing.Any) -> typing.TypeGuard[Self]:
        """
        Check if this sentinel value is not equal to another object.

        Parameters
        ----------
        other : typing.Any
            The object to compare with this sentinel value.

        Returns
        -------
        bool
            True if the other object is not a sentinel value or has a different name,
            False otherwise.

        """
        return not (self == other)

    @override
    def __hash__(self) -> int:
        """
        Compute a hash value for this sentinel value.

        Returns
        -------
        int
            The hash value.

        """
        return hash(self.__name__)

    @override
    def __repr__(self) -> str:
        """
        Get a string representation of this sentinel value.

        Returns
        -------
        str
            The string representation.

        """
        return f"?{self.__name__}"

    def __contains__(self, other: typing.Any) -> typing.TypeGuard[Self]:
        return self.is_missing(other)

    def is_value(self, other: _O | Self) -> typing.TypeGuard[_O]:
        return not self.is_missing(other)

    def is_missing(self, other: typing.Any | Self) -> typing.TypeGuard[Self]:
        return other is self

    def guard_as(self, other: _O | Self, fn: typing.Callable[[Self], _O]) -> _O:
        if self.is_value(other):
            return other
        else:
            return fn(other)

    @classmethod
    def Error(cls):
        return TypeError(f"value is {cls.__name__}!")
