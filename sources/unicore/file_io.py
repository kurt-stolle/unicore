"""
Implements a path manager for UniCore using IoPath.
"""

from __future__ import annotations

import functools
import os
import typing
import warnings
from pathlib import Path as _PathlibPath

from iopath.common.file_io import (
    HTTPURLHandler,
    OneDrivePathHandler,
    PathHandler,
    PathManager,
    PathManagerFactory,
)
from typing_extensions import override

from unicore.utils.iopathlib import IoPath

__all__ = ["Path"]


_manager: typing.Final = PathManagerFactory.get(defaults_setup=False)


class Path(IoPath, manager=_manager):
    """
    See ``IoPath``.
    """


class EnvPathHandler(PathHandler):
    """
    Resolve prefix, e.g. `prefix://`, to environment variable PREFIX.
    """

    def __init__(self, prefix: str, env: str, default: str | None = None):
        value = os.getenv(env)
        if value is None or len(value) == 0 or value[0] == "-":
            if default is None:
                raise ValueError(f"Environment variable {env} not defined!")
            warnings.warn(f"Environment variable {env} not defined, using default {default!r}.", stacklevel=2)
            value = default

        self.PREFIX: typing.Final = prefix
        self.LOCAL: typing.Final = value

    @override
    def _get_supported_prefixes(self):
        return [self.PREFIX]

    def _get_path(self, path: str, **kwargs) -> _PathlibPath:
        name = path[len(self.PREFIX) :]
        if len(name) == 0:
            return _PathlibPath(self.LOCAL).resolve()
        else:
            return _PathlibPath(self.LOCAL, *name.split("/")).resolve()

    @override
    def _get_local_path(self, path: str, **kwargs):
        return str(self._get_path(path, **kwargs))

    @override
    def _isfile(self, path: str, **kwargs: typing.Any) -> bool:
        return self._get_path(path, **kwargs).is_file()

    @override
    def _isdir(self, path: str, **kwargs: typing.Any) -> bool:
        return self._get_path(path, **kwargs).is_dir()

    @override
    def _ls(self, path: str, **kwargs: typing.Any) -> list[str]:
        return sorted(p.name for p in self._get_path(path, **kwargs).iterdir())

    @override
    def _open(self, path: str, mode="r", **kwargs):
        # name = path[len(self.PREFIX) :]
        # return _g_manager.open(self.LOCAL + name, mode, **kwargs)
        return open(self._get_local_path(path), mode, **kwargs)


for h in (
    OneDrivePathHandler(),
    HTTPURLHandler(),
    EnvPathHandler("//datasets/", "UNICORE_DATASETS", "./datasets"),
    EnvPathHandler("//cache/", "UNICORE_CACHE", "./cache"),
    EnvPathHandler("//output/", "UNICORE_OUTPUT", "./output"),
    EnvPathHandler("//scratch/", "UNICORE_SCRATCH", "./scratch")
):
    _manager.register_handler(h, allow_override=False)
_exports: frozenset[str] = frozenset(fn_name for fn_name in dir(_manager) if not fn_name.startswith("_"))


_Params = typing.ParamSpec("_Params")
_Return = typing.TypeVar("_Return")
_PathCallable: typing.TypeAlias = typing.Callable[typing.Concatenate[str, _Params], _Return]


def with_local_path(
    fn: _PathCallable | None = None,
    *,
    manager: PathManager = _manager,
    **get_local_path_kwargs: typing.Any,
) -> _PathCallable | typing.Callable[[_PathCallable], _PathCallable]:
    """
    Decorator that converts the first argument of a function to a local path.

    This is useful for functions that take a path as the first argument, but
    the path is not necessarily local. This decorator will convert the path
    to a local path using the path manager, and pass the result to the function.

    Parameters
    ----------
    fn : Callable
        The function to decorate.
    manager : PathManager, optional
        The path manager to use, by default the default path manager.
    **get_local_path_kwargs : Any
        Keyword arguments to pass to the path manager's ``get_local_path`` method.

    Returns
    -------
    Callable
        The decorated function.

    """

    if fn is None:
        return functools.partial(with_local_path, manager=manager, **get_local_path_kwargs)  # type: ignore

    @functools.wraps(fn)
    def Wrapper(path: str, *args: _Params.args, **kwargs: _Params.kwargs):
        path = manager.get_local_path(path, **get_local_path_kwargs)
        return fn(path, *args, **kwargs)

    return Wrapper


def __getattr__(name: str):
    global _manager
    global _exports
    if name in _exports:
        return getattr(_manager, name)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    global _exports
    return __all__ + list(_exports)
