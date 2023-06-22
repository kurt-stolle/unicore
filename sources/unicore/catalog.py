from __future__ import annotations

import functools
import re
import types
import typing as T
from typing import final

from typing_extensions import Self

from unicore.utils.dataset import Dataset
from unicore.utils.registry import Registry

__all__ = ["DataManager", "InfoFunc", "Info", "KeyLike"]


class Info(T.Hashable):
    """
    A class containing information about a dataset, also know as the dataset's metadata.
    """


InfoFunc: T.TypeAlias = T.Callable[[], Info]
KeyLike: T.TypeAlias = type | str | T.Callable[..., T.Any]

_D = T.TypeVar("_D")
_D_co = T.TypeVar("_D_co", covariant=True)

_STR_TO_KEY = re.compile(r"(?<=[a-z])(?=[A-Z])|[^a-zA-Z]")


class _DataManagerBase(T.Generic[_D_co]):
    @staticmethod
    def _infer_id(other: KeyLike) -> str:
        if isinstance(other, types.LambdaType):
            raise ValueError("Cannot infer ID from lambda function")

        name = other if isinstance(other, str) else other.__name__

        def _to_snake_case(s: str) -> str:
            return "".join(_STR_TO_KEY.sub(" ", s).strip().replace(" ", "_").lower())

        name = "/".join(_to_snake_case(s) for s in name.split("/"))

        return name

    def __init__(self):
        self._info: Registry[T.Any] = Registry()
        self._data: Registry[type[_D_co]] = Registry()

    def _get_data(self, key: str, /) -> type[_D_co]:
        return self._data[key]

    def _get_info(self, key: str, /) -> T.Callable[[], Info]:
        return self._info[key]()

    def __ior__(self, __other: _DataManagerBase, /) -> Self:
        """
        Merge the data and info registries of this manager with another.
        The other manager takes precedence in case of conflicts.
        """
        self._data |= __other._data
        self._info |= __other._info

        return self

    def __or__(self, __other: _DataManagerBase, /) -> Self:
        from copy import copy

        obj = copy(self)
        obj |= __other

        return obj


def _read_info_at(dataset: type[Dataset]) -> Info:
    return dataset.read_info()


@final
class DataManager(_DataManagerBase[Dataset]):
    """
    Data manager for registering datasets and their info functions. This is a singleton object that can be imported from
    the unicore.catalog module, and it is recommended to use this object instead of creating new data managers.
    """

    def fork(self) -> DataManager:
        """
        Return a copy of this data manager.
        """
        return DataManager() | self

    def register_dataset(
        self, id: str | None = None, *, info: T.Optional[T.Callable[[], Info]] = None
    ) -> T.Callable[[type[Dataset]], type[Dataset]]:
        """
        Register a dataset.

        Parameters
        ----------
        id : Optional[str]
            The ID to register the dataset with. If None, the dataset class name will be used (flattened and converted
            to snake_case).
        """

        def wrapped(ds: type[Dataset]) -> type[Dataset]:
            key = id or self._infer_id(ds)
            if key in self.list_datasets():
                raise KeyError(f"Already registered: {key}")
            if key in self.list_info():
                raise KeyError(f"Already registered as info: {key}. Dataset keys cannot be dually registered.")

            self._data[key] = ds

            if info is None:
                info_fn = functools.partial(_read_info_at, ds)
            else:
                info_fn = info
            if callable(info_fn):
                self._info[key] = info_fn
            else:
                raise TypeError(f"Invalid info function: {info_fn}")

            return ds

        return wrapped

    def get_dataset(self, id: str) -> type[Dataset]:
        """
        Return the dataset class for the given dataset ID.
        """
        key = self._infer_id(id)
        return self._get_data(key)

    def list_datasets(self) -> frozenset[str]:
        """
        Return a frozenset of all registered dataset IDs.
        """
        return self._data.list()

    def register_info(
        self,
        id_: str,
        /,
    ) -> T.Callable[[InfoFunc], T.Callable[[], Info]]:
        """
        Register a dataset.

        Parameters
        ----------
        id : Optional[str]
            The ID to register the dataset with. If None, the dataset class name will be used (flattened and converted
            to snake_case).
        """

        def wrapped(info: InfoFunc) -> T.Callable[[], Info]:
            # info_list = []
            # info_list.append(info if callable(info) else lambda: info)
            # if len(extra_info) > 0:
            #     info_list.append(lambda: extra_info)

            self._info[id_] = info

            return functools.partial(self.get_info, id_)

        return wrapped

    def get_info(self, id: KeyLike) -> Info:
        """
        Return the info for the given dataset ID.
        """
        key = self._infer_id(id)
        return self._get_info(key)()

    def list_info(self) -> frozenset[str]:
        """
        Return a frozenset of all registered dataset IDs.
        """
        return self._info.list()


_DATA_MANAGER: T.Final[DataManager] = DataManager()
_EXPORTS: frozenset[str] = frozenset(fn_name for fn_name in dir(DataManager) if not fn_name.startswith("_"))


def __getattr__(name: str):
    if name in _EXPORTS:
        return getattr(_DATA_MANAGER, name)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return __all__ + list(_EXPORTS)
