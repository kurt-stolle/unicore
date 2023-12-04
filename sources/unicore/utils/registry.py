from __future__ import annotations

import weakref
import functools
from typing import Callable, Concatenate, Generic, Iterator, ParamSpec, TypeVar, Optional, Hashable

from typing_extensions import Self, override

__all__ = ["Registry"]  # , "WeakLazyRegistry"]

_T = TypeVar("_T", bound=Hashable)
_I = TypeVar("_I", bound=Hashable)
_P = ParamSpec("_P")
_R = TypeVar("_R")


class Registry(Generic[_T, _I]):
    __slots__ = ["__dict__", "to_id"]
    to_id: Optional[Callable[[_I], str]]

    def __init__(self, canonicalizer: Optional[Callable[[_I], str]] = None) -> None:
        self.to_id = canonicalizer

    @property
    def keys(self):
        return self.__dict__.keys

    @staticmethod
    def _with_canonical_id(
        fn: Callable[Concatenate[Registry, str, _P], _R]
    ) -> Callable[Concatenate[Registry, _I, _P], _R]:
        """
        Decorator method that dispatches the ID to the canonicalizer, if present.
        """

        @functools.wraps(fn)
        def wrapped(obj: Registry, id: _I, /, *args: _P.args, **kwargs: _P.kwargs) -> _R:
            if obj.to_id is not None:
                key = obj.to_id(id)
            else:
                key = str(id)
            return fn(obj, key, *args, **kwargs)

        return wrapped

    @_with_canonical_id
    def __getitem__(self, __key: str, /) -> _T:
        return self.__dict__[__key]

    @_with_canonical_id
    def __setitem__(self, __key: str, value: _T, /) -> None:
        if __key in self:
            raise KeyError(f"Already registered: {id}")
        self.__dict__[__key] = value

    @_with_canonical_id
    def __delitem__(self, __key: str, /) -> None:
        del self.__dict__[__key]

    @_with_canonical_id
    def __contains__(self, __key: str, /) -> bool:
        return __key in self.__dict__

    def __iter__(self) -> Iterator[str]:
        yield from self.__dict__.keys()

    def __len__(self) -> int:
        return len(self.__dict__)

    def __or__(self, other: Registry) -> Self:
        if not self.to_id == other.to_id:
            raise ValueError("Cannot merge registries with different canonicalizers.")

        new = self.__class__(self.to_id)
        new.__dict__ = {**self.__dict__, **other.__dict__}

        return new

    def __ior__(self, other: Registry) -> Self:
        if not self.to_id == other.to_id:
            raise ValueError("Cannot merge registries with different canonicalizers.")

        self.__dict__.update(other.__dict__)
        return self

    @_with_canonical_id
    def register(self, __key: str, /) -> Callable[[_T], _T]:
        def decorator(value: _T) -> _T:
            self[__key] = value
            return value

        return decorator


# _L = TypeVar("_L")


# class WeakLazyRegistry(Registry[Callable[[], _L]], Generic[_L]):
#     __slots__ = ["_active"]

#     _active: weakref.WeakValueDictionary[str, _L]

#     def __init__(self) -> None:
#         super().__init__()
#         self._active = weakref.WeakValueDictionary()

#     @override
#     def __setitem__(self, id: str, value: Callable[[], _L]) -> None:
#         return super().__setitem__(id, value)

#     @override
#     def __getitem__(self, id: str, /) -> _L:
#         if id in self._active:
#             return self._active[id]

#         item = self._active[id] = self.storage[id]()
#         return item

#     @override
#     def __delitem__(self, __key: str, /) -> None:
#         super().__delitem__(__key)
#         if __key in self._active:
#             del self._active[__key]

#     @override
#     def __len__(self) -> int:
#         return len(self.storage)

#     @override
#     def __contains__(self, id: str) -> bool:
#         return id in self.storage

#     @override
#     def __iter__(self) -> Iterator[str]:
#         return self._active.keys()
