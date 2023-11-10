"""
Utility to create a `tensordict`-like tensorclass using a superclass instead of
the provided decorator `@tensorclass`.

This is useful when you want typing to work properly, and is more explicit.
"""

from __future__ import annotations

import types
import typing as T

import torch.utils._pytree as pytree
from tensordict import TensorDict, TensorDictBase, tensorclass
from typing_extensions import override

__all__ = ["Tensorclass", "TypedTensorDict", "TensorDict", "TensorDictBase"]
__dir__ = ["Tensorclass", "TypedTensorDict", "TensorDict", "TensorDictBase"]


# @T.dataclass_transform()
class TensorclassMeta(type):
    """
    TensorclassMeta is a metaclass that wraps the `@tensorclass` decorator around the child.
    """

    def __new__(cls, name: str, bases: tuple[type, ...], ns: dict[str, T.Any], **kwds):
        # if len(bases) == 0:
        #     return super().__new__(cls, name, tuple(bases), ns, **kwds)

        bases = types.resolve_bases(bases)
        tc = super().__new__(cls, name, tuple(bases), ns, **kwds)
        tc = tensorclass(tc)  # type: ignore

        return tc

    @override
    def __instancecheck__(cls, ins: T.Any) -> bool:
        return isinstance(ins, TensorDictBase) or super().__instancecheck__(ins)

    @override
    def __subclasscheck__(cls, sub: T.Any) -> bool:
        return issubclass(sub, TensorDictBase) or super().__subclasscheck__(sub)


@T.dataclass_transform()
class Tensorclass(metaclass=TensorclassMeta):
    """
    Tensorclass is a class that allows you to create a `tensordict`-like
    tensorclass using a superclass instead of the provided decorator `@tensorclass`.
    """

    def __post_init__(self):
        pass

    def _flatten(self) -> T.Tuple[T.List[T.Any], pytree.Context]:
        values = []
        values += list(self._tensordict.values())  # type: ignore
        values += list(self._non_tensordict.values())  # type: ignore

        keys = []
        keys += list(self._tensordict.keys())
        keys += list(self._non_tensordict.keys())

        context = {
            "keys": keys,
            "batch_size": self.batch_size,
            # "names": self.names,
        }

        return values, context

    @classmethod
    def stack(cls, *others: T.Self) -> T.Self:
        """
        Stacks multiple tensorclasses together.
        """
        if len(others) == 0:
            raise ValueError("Must provide at least one tensorclass to stack.")

        if len(others) == 1:
            return others[0]

        td = torch.stack(others)  # type: ignore
        return cls.from_tensordict(td)

    @classmethod
    def _unflatten(cls, values: T.List[T.Any], context: pytree.Context) -> T.Self:
        obj = cls(
            **dict(zip(context["keys"], values)),
            batch_size=context["batch_size"],
            # names=context["names"],
        )
        return obj

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        pytree._register_pytree_node(cls, cls._flatten, cls._unflatten)


_TensorDictType = T.TypeVar("_TensorDictType", bound=TensorDictBase)


class TypedTensorDict(TensorDict, T.Generic[_TensorDictType]):
    __slots__ = ()

    def to_dict(self) -> _TensorDictType:
        raise NotImplementedError()

    def __class_getitem__(cls, item):
        raise NotImplementedError()

    if not T.TYPE_CHECKING:

        def __new__(cls, *args, **kwargs) -> TensorDict:
            return TensorDict(*args, **kwargs)
