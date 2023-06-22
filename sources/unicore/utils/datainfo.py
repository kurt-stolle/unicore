"""
Various descriptors for dataset info (metadata about the dataset)
"""

import abc
import dataclasses
from types import resolve_bases
from typing import Any, Callable, Final, Generic, Iterable, TypeAlias, TypeVar

from typing_extensions import final, override

__all__ = ["infomethod", "infodescriptor"]

MARKER: Final = "__" + "_".join(n for n in __name__.split("_") if n) + "__"

_T = TypeVar("_T", bound=Any)  # generic (any)
_T_co = TypeVar("_T_co", covariant=True, bound=Any)
_T_cn = TypeVar("_T_cn", contravariant=True, bound=Any)
_R = TypeVar("_R", covariant=True, bound=Any)  # return value
_R_cn = TypeVar("_R_cn", contravariant=True, bound=Any)
_F: TypeAlias = Callable[[], _R_cn]  # function
_F_co = TypeVar("_F_co", covariant=True, bound=Callable)


def discover_info(__cls: Any) -> Iterable[Any]:
    if len(__cls.__dict__) == 0:
        yield from ()
        return

    for obj in __cls.__dict__.items():
        info_mthd = getattr(obj, MARKER, None)
        if info_mthd is not None:
            yield info_mthd


class _InfoDescriptor(abc.ABCMeta):
    @override
    @classmethod
    def __prepare__(cls, name: str, bases: tuple[type, ...]) -> object:
        return {MARKER: None, "__slots__": tuple()}

    def __new__(mcls, name, bases, ns, **kwds):
        bases = resolve_bases(bases)
        cls = super().__new__(mcls, name, bases, ns, **kwds)
        cls.__hash__ = bases[-1].__hash__  # type: ignore
        cls = dataclasses.dataclass(slots="__slots__" not in ns)(cls)  # type: ignore

        return cls


@final  # use metaclass instead
class infodescriptor(abc.ABC, metaclass=_InfoDescriptor):
    pass


@final  # use metaclass instead
class infomethod(Generic[_T, _R], metaclass=_InfoDescriptor):
    """
    Declare a data info function
    """

    def __init__(self, fn: _F[_R]):
        self._fn: Final = fn
        self._name = fn.__name__

    @property
    def name(self):
        return self._name

    @property
    @override
    def __doc__(self):
        return self._fn.__doc__

    def __set_name__(self, owner: type, name: str):
        self._name = name

    def __get__(self, ins: object | None, owner: type) -> _F[_R]:
        return self._fn

    def __call__(self, *args, **kwds) -> _R:
        return self._fn(*args, **kwds)
