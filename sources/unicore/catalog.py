from __future__ import annotations

import functools
import re
import types
import typing as T

from unicore.utils.dataset import Dataset
from unicore.utils.registry import Registry

__all__ = ["DataManager"]


DEFAULT_ID_PATTERN: T.Final[re.Pattern] = re.compile(r"^[a-z\d\-]+$")

_D_co = T.TypeVar("_D_co", covariant=True)
_I_co = T.TypeVar("_I_co", covariant=True)
_P = T.ParamSpec("_P")


@T.final
class DataManager(T.Generic[_D_co, _I_co]):
    """
    Data manager for registering datasets and their info functions.
    """

    def __init__(self, *, id_pattern: re.Pattern = DEFAULT_ID_PATTERN, variant_separator: str = "/"):
        self._variant_separator: T.Final[str] = variant_separator
        self._id_pattern: T.Final[str] = id_pattern
        self._info: T.Final[Registry[_I_co, _D_co | str]] = Registry(self.parse_key)
        self._data: T.Final[Registry[type[_D_co], _D_co | str]] = Registry(self.parse_key)

    def parse_key(self, key: str, *, check_valid: bool = True) -> str:
        """
        Convert a string or class to a canonical ID.

        Parameters
        ----------
        other : Union[str, type]
            The string or class to convert.

        Returns
        -------
        str
            The canonical ID.
        """
        id_ = key if isinstance(key, str) else key.__name__.replace("Dataset", "")
        id_ = id_.lower()
        if check_valid and not self._id_pattern.match(id_):
            raise ValueError(f"{id_} does not match {self._id_pattern.pattern}")

        return id_

    def split_query(self, query: str) -> tuple[str, list[str]]:
        """
        Split a query into a dataset ID and a variant ID.
        """
        if self._variant_separator not in query:
            return query, []
        else:
            key, variant = query.split(self._variant_separator)
            return key, variant

    def __ior__(self, __other: DataManager, /) -> T.Self:
        """
        Merge the data and info registries of this manager with another.
        The other manager takes precedence in case of conflicts.
        """
        self._data |= __other._data
        self._info |= __other._info

        return self

    def __or__(self, __other: DataManager, /) -> T.Self:
        from copy import copy

        obj = copy(self)
        obj |= __other

        return obj

    def fork(self) -> DataManager:
        """
        Return a copy of this data manager.
        """
        return DataManager() | self

    # -------- #
    # DATASETS #
    # -------- #

    def register_dataset(
        self, id: str | None = None, *, info: T.Optional[T.Callable[..., _I_co]] = None
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
            key = id or self.parse_key(ds)
            if key in self.list_datasets():
                raise KeyError(f"Already registered: {key}")
            if key in self.list_info():
                raise KeyError(f"Already registered as info: {key}. Dataset keys cannot be dually registered.")

            self._data[key] = ds

            if info is None:
                raise ValueError(f"Dataset {key} has no info function and no info function was provided.")
            if callable(info):
                self._info[key] = info
            else:
                raise TypeError(f"Invalid info function: {info}")

            return ds

        return wrapped

    def get_dataset(self, query: str) -> type[Dataset]:
        """
        Return the dataset class for the given dataset ID.
        """
        return self._data[query]

    def list_datasets(self) -> list[str]:
        """
        Return a frozenset of all registered dataset IDs.
        """
        return list(self._data.keys())

    # ---- #
    # Info #
    # ---- #

    def register_info(
        self,
        id_: str | _D_co,
        /,
    ) -> T.Callable[[T.Callable[_P, _I_co]], T.Callable[_P, _I_co]]:
        """
        Register a dataset.

        Parameters
        ----------
        id : Optional[str]
            The ID to register the dataset with. If None, the dataset class name will be canonicalized using
            ``canonicalize_id``.
        """

        def wrapped(info: T.Callable[_P, _I_co]) -> T.Callable[_P, _I_co]:
            self._info[id_] = info

            return functools.partial(self.get_info, id_)

        return wrapped

    def get_info(self, query: str) -> _I_co:
        """
        Return the info for the given dataset ID.
        """
        return self._info[query]()

    def list_info(self) -> list[str]:
        """
        Return a frozenset of all registered dataset IDs.
        """
        return list(self._info.keys())
