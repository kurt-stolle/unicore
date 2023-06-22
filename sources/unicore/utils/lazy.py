"""
Utilities related to caching of expensive operations.
"""
from __future__ import annotations

import functools
import weakref
from threading import RLock
from typing import (
    Any,
    Callable,
    Final,
    Generic,
    Optional,
    TypeAlias,
    TypeVar,
    cast,
    overload,
)

from typing_extensions import Self, final, override

from unicore.utils.missing import MissingValue

# __all__ = ["with_lazy_slots", "lazyproperty"]
__all__ = ["lazyproperty"]


# def _get_slots(ns: Mapping[str, Any]):
#     match ns.get("__slots__", None):
#         case None:
#             return
#         case str(slot):
#             yield slot
#         # Slots may be any iterable, but we cannot handle an iterator
#         # because it will already be (partially) consumed.
#         case iterable if not hasattr(iterable, "__next__"):
#             yield from iterable
#         case _:
#             raise TypeError("Slots cannot be determined")


# def _get_lazy_targets(ns: Mapping[str, Any]) -> Iterator[str]:
#     return itertools.filterfalse(
#         ns.__contains__, (str(attr.to) for attr in ns.values() if isinstance(attr, lazyproperty))
#     )


# def build_lazy_slots(ns: MutableMapping[str, Any], bases: tuple[type, ...]) -> Iterator[str]:
#     """
#     Infer the `__slots__` attribute for a given namespace by inspecting the namespace
#     for `lazy` descriptors
#     """
#     yield from itertools.filterfalse(
#         # Parent slots
#         set(
#             itertools.chain.from_iterable(
#                 map(
#                     _get_slots,
#                     map(operator.attrgetter("__dict__"), bases),
#                 ),
#             )
#         ).__contains__,
#         # Targets of each lazy property
#         _get_lazy_targets(ns),
#     )


# _C = TypeVar("_C", bound=object)


# @overload
# def with_lazy_slots(
#     __cls: type[_C],
#     /,
#     *,
#     with_dict: Literal["auto", "never", "always"] = "auto",
# ) -> type[_C]:
#     ...


# @overload
# def with_lazy_slots(
#     __cls=None,
#     /,
#     *,
#     with_dict: Literal["auto", "never", "always"] = "auto",
# ) -> Callable[[_C], _C]:
#     ...


# def with_lazy_slots(
#     __cls: Optional[type[_C]] = None,
#     /,
#     *,
#     with_dict: Literal["auto", "never", "always"] = "auto",
# ) -> type[_C] | Callable[[_C], _C]:
#     def decorator(cls):
#         slots = set()
#         slots |= set(getattr(cls, "__slots__", tuple()))
#         slots |= set(build_lazy_slots(cls.__dict__, cls.__mro__[0:-1]))

#         # Remove existing weakref
#         if "__weakref__" in cls.__dict__:
#             slots.add("__weakref__")

#         # Maybe add __dict__ to __slots__
#         match with_dict:
#             case "auto":
#                 if not hasattr(cls, "__slots__") or not with_dict:
#                     # Add a __dict__ slot, because the class did not explicitly define its own __slots__
#                     slots.add("__dict__")
#             case "always":
#                 slots.add("__dict__")
#             case "never":
#                 pass

#         cls_dict = dict(cls.__dict__)
#         cls_dict.pop("__dict__", None)  # Remove __dict__ itself
#         for slot in slots:
#             cls_dict.pop(slot, None)
#         cls_dict["__slots__"] = tuple(slots)

#         qualname = getattr(cls, "__qualname__", None)
#         cls = type(cls)(cls.__name__, cls.__bases__, cls_dict)
#         if qualname is not None:
#             cls.__qualname__ = qualname

#         abc.update_abstractmethods(cls)

#         return cls

#     if __cls is None:
#         return decorator
#     else:
#         return decorator(__cls)


_T = TypeVar("_T", bound=Any)
_R = TypeVar("_R", covariant=True)
_F: TypeAlias = Callable[[Any], _R]


@final
class lazyproperty(Generic[_T, _R]):
    """
    Defines a property a la `functools.cached_property` that is stored at a specific attribute
    on the parent class. Useful for classes that are required to define `__slots__` and thus
    do not trivially have a `__dict__` available to stored cached items.
    """

    __slots__ = ("fn", "to", "lock", "store")

    @overload
    def __new__(cls, fn: _F[_R], /, to: Optional[str] = None) -> Self:
        ...

    @overload
    def __new__(cls, fn=None, /, to: Optional[str] = None) -> Callable[[_F[_R]], Self]:
        ...

    def __new__(cls, fn: Optional[_F[_R]] = None, /, to: Optional[str] = None) -> Self | Callable[[_F[_R]], Self]:
        if fn is None:
            return functools.partial(cls, to=to)
        else:
            return super().__new__(cls)

    @property
    @override
    def __doc__(self):
        return self.fn.__doc__

    def __init__(self, fn: Optional[_F[_R]] = None, /, to: Optional[str] = None):
        if fn is None:
            raise ValueError(f"{type(self).__name__} cannot be initialized without a wrappig function!")
        self.fn: Final = fn
        self.lock: Final = RLock()
        self.store = weakref.WeakKeyDictionary()

    def __set_name__(self, owner, name):
        if name != self.fn.__name__:
            raise ValueError(f"property name {name} is not equal to function name {self.fn.__name__}!")

    @overload
    def __get__(self, obj: Any, owner: Optional[type] = None, /) -> _R:
        ...

    @overload
    def __get__(self, obj=None, owner: Optional[type] = None, /) -> Self:
        ...

    def __get__(self, obj: Any | None = None, owner: Optional[type] = None, /) -> _R | Self:
        if obj is None:
            return self
        item = self.store.get(obj)
        if item is not None:
            return item
        item = self(obj)
        if item is None:
            raise RuntimeError(f"Lazy property {self.fn.__name__} returned None!")
        return item

    def __delete__(self, obj: Any, **kwargs) -> None:
        with self.lock:
            del self.store[obj]

    def __set__(self, *args, **kwargs) -> None:
        raise AttributeError(f"{type(self).__name__} does not support assignment!")

    def __call__(self, obj: Any, *, force_reload=False) -> _R:
        if force_reload and obj in self.store:
            del self.store[obj]
        with self.lock:
            # check if another thread filled cache while we awaited lock
            value = self.store.get(obj)
            if value is not None:
                return cast(_R, value)

            value = self.fn(obj)

            self.store[obj] = value
        return value
