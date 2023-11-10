from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Self,
    Sequence,
    TypeAlias,
    TypeVar,
)

from unicore.utils.dataset import Dataset
from unicore.utils.frozendict import frozendict

InfoBasic: TypeAlias = str | int | bool | float
InfoItem: TypeAlias = InfoBasic | Sequence[InfoBasic]
InfoFunc: TypeAlias = Callable[[], dict[str, InfoBasic | Sequence[InfoBasic]]]
Info: TypeAlias = InfoFunc | dict[str, InfoBasic]
KeyLike: TypeAlias = type | str | Callable[..., Any]

def canonicalize_id(id: KeyLike) -> str: ...

_D = TypeVar("_D", bound=Dataset)
_D_co = TypeVar("_D_co", bound=Dataset, covariant=True)

def fork() -> Self: ...
def register_dataset(id: str | None = None) -> Callable[[type[_D]], type[_D]]: ...
def get_dataset(id: str) -> type[_D]: ...
def list_datasets() -> frozenset[str]: ...
def register_info(id: str | None = None, /) -> Callable[[InfoFunc], Callable[[], Mapping[str, Any]]]: ...
def get_info(id: KeyLike) -> Any: ...
def list_info() -> frozenset[str]: ...
