from __future__ import annotations

import weakref
from typing import Callable, Generic, Iterator, TypeVar

from typing_extensions import Self, override

__all__ = ["Registry", "WeakLazyRegistry"]

_T = TypeVar("_T")


class Registry(Generic[_T]):
    __slots__ = ["_items"]

    _items: dict[str, _T]

    def __init__(self) -> None:
        self._items = {}

    def list(self) -> frozenset[str]:
        return frozenset(self._items.keys())

    # @override
    def __getitem__(self, id: str, /) -> _T:
        return self._items[id]

    # @override
    def __setitem__(self, id: str, value: _T, /) -> None:
        if id in self._items:
            raise KeyError(f"Already registered: {id}")
        self._items[id] = value

    # @override
    def __delitem__(self, __key: str, /) -> None:
        del self._items[__key]

    # @override
    def __iter__(self) -> Iterator[str]:
        yield from self._items.keys()

    # @override
    def __len__(self) -> int:
        return len(self._items)

    # @override
    def __contains__(self, id: str) -> bool:
        return id in self._items

    def __or__(self, other: Registry) -> Self:
        new = type(self)()
        new._items = {**self._items, **other._items}

        return new

    def register(self, id: str) -> Callable[[_T], _T]:
        def decorator(value: _T) -> _T:
            self[id] = value
            return value

        return decorator


_L = TypeVar("_L")


class WeakLazyRegistry(Registry[Callable[[], _L]], Generic[_L]):
    __slots__ = ["_active"]

    _active: weakref.WeakValueDictionary[str, _L]

    def __init__(self) -> None:
        super().__init__()
        self._active = weakref.WeakValueDictionary()

    @override
    def __setitem__(self, id: str, value: Callable[[], _L]) -> None:
        return super().__setitem__(id, value)

    @override
    def __getitem__(self, id: str, /) -> _L:
        if id in self._active:
            return self._active[id]

        item = self._active[id] = self._items[id]()
        return item

    @override
    def __delitem__(self, __key: str, /) -> None:
        super().__delitem__(__key)
        if __key in self._active:
            del self._active[__key]

    @override
    def __len__(self) -> int:
        return len(self._items)

    @override
    def __contains__(self, id: str) -> bool:
        return id in self._items

    @override
    def __iter__(self) -> Iterator[str]:
        return self._active.keys()
