"""
Implements a path manager for UniCore using IoPath.
"""

from __future__ import annotations

import functools
import io
import os
import typing as T
import uuid
import warnings
from pathlib import Path as _PathlibPath
from urllib.parse import ParseResult, urlparse

import typing_extensions as TX
import wandb
from iopath import file_lock
from iopath.common.file_io import (
    HTTPURLHandler,
    OneDrivePathHandler,
    PathHandler,
    PathManager,
    PathManagerFactory,
)

from unicore.utils.iopathlib import IoPath

__all__ = ["Path"]


################
# Path manager #
################

_manager: T.Final = PathManagerFactory.get(defaults_setup=False)


#################
# Path subclass #
#################
class Path(IoPath, manager=_manager):
    """
    See ``IoPath``.
    """


#################
# Path handlers #
#################


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

        self.PREFIX: T.Final = prefix
        self.LOCAL: T.Final = value

    @TX.override
    def _get_supported_prefixes(self):
        return [self.PREFIX]

    def _get_path(self, path: str, **kwargs) -> _PathlibPath:
        name = path[len(self.PREFIX) :]
        if len(name) == 0:
            return _PathlibPath(self.LOCAL).resolve()
        else:
            return _PathlibPath(self.LOCAL, *name.split("/")).resolve()

    @TX.override
    def _get_local_path(self, path: str, **kwargs):
        return str(self._get_path(path, **kwargs))

    @TX.override
    def _isfile(self, path: str, **kwargs: T.Any) -> bool:
        return self._get_path(path, **kwargs).is_file()

    @TX.override
    def _isdir(self, path: str, **kwargs: T.Any) -> bool:
        return self._get_path(path, **kwargs).is_dir()

    @TX.override
    def _ls(self, path: str, **kwargs: T.Any) -> list[str]:
        return sorted(p.name for p in self._get_path(path, **kwargs).iterdir())

    @TX.override
    def _open(self, path: str, mode="r", **kwargs):
        # name = path[len(self.PREFIX) :]
        # return _g_manager.open(self.LOCAL + name, mode, **kwargs)
        return open(self._get_local_path(path), mode, **kwargs)


class WandBArtifactHandler(PathHandler):
    """
    Handles pulling artifacts from W&B using the API.
    """

    def __init__(self):
        super().__init__()
        self.cache_map: dict[str, str] = {}

    def _parse_path(self, path: str) -> tuple[str, str | None]:
        """
        Format is one of the following:
         - wandb-artifact:///entity/project/name:version/file.h5
         - wandb-artifact:///entity/project/name:version
         - wandb-artifact://project/name:version/file.h5
        """
        url = urlparse(path)

        assert url.scheme == "wandb-artifact", f"Unsupported scheme {url.scheme!r}"

        # Spit by : to get name and combined version/file
        name, version_file = url.path.split(":")

        # Split by / to get version and filepath
        version, *maybe_file = version_file.split("/", 1)
        if len(maybe_file) > 0:
            file = maybe_file[0]
        else:
            file = None

        if len(url.netloc) > 0:
            name = f"{url.netloc}/{name}"
        elif name.startswith("/"):
            name = name[1:]

        name = f"{name}:{version}"

        # Name is the netloc + name, where netloc could be empty
        return name, file

    def _get_artifact(self, name: str) -> wandb.Artifact:
        return wandb.Api().artifact(name)

    @TX.override
    def _get_supported_prefixes(self) -> list[str]:
        return ["wandb-artifact://"]

    @TX.override
    def _get_local_path(self, path: str, mode: str = "r", force: bool = False, **kwargs):
        self._check_kwargs(kwargs)

        assert mode in ("r",), f"Unsupported mode {mode!r}"

        if force or path not in self.cache_map or not os.path.exists(self.cache_map[path]):
            name, file = self._parse_path(path)
            artifact = self._get_artifact(name)

            path = _manager.get_local_path(f"//cache/wandb-artifact/{name}")
            with file_lock(path):
                if not os.path.exists(path) or force:
                    path = artifact.checkout(path)
                elif os.path.isfile(path):
                    raise FileExistsError(f"A file exists at {path!r}")
            path = os.path.join(path, file) if file is not None else path

            self.cache_map[path] = path
        return self.cache_map[path]

    @TX.override
    def _open(self, path: str, mode: str = "r", buffering: int = -1, **kwargs: T.Any) -> T.IO[str] | T.IO[bytes]:
        """
        Open a remote HTTP path. The resource is first downloaded and cached
        locally.

        Args:
            path (str): A URI supported by this PathHandler
            mode (str): Specifies the mode in which the file is opened. It defaults
                to 'r'.
            buffering (int): Not used for this PathHandler.

        Returns:
            file: a file-like object.
        """
        self._check_kwargs(kwargs)
        assert mode in ("r", "rb"), "{} does not support open with {} mode".format(self.__class__.__name__, mode)
        assert buffering == -1, f"{self.__class__.__name__} does not support the `buffering` argument"
        local_path = self._get_local_path(path, force=False)
        return open(local_path, mode)


# Register handlers with the manager object
for h in (
    OneDrivePathHandler(),
    HTTPURLHandler(),
    WandBArtifactHandler(),
    EnvPathHandler("//datasets/", "UNICORE_DATASETS", "./datasets"),
    EnvPathHandler("//cache/", "UNICORE_CACHE", "~/.torch/unicore_cache"),
    EnvPathHandler("//output/", "UNICORE_OUTPUT", "./output"),
    EnvPathHandler("//scratch/", "UNICORE_SCRATCH", "./scratch"),
):
    _manager.register_handler(h, allow_override=False)
_exports: frozenset[str] = frozenset(fn_name for fn_name in dir(_manager) if not fn_name.startswith("_"))

##############
# Decorators #
##############

_Params = T.ParamSpec("_Params")
_Return = T.TypeVar("_Return")
_PathCallable: T.TypeAlias = T.Callable[T.Concatenate[str, _Params], _Return]


def with_local_path(
    fn: _PathCallable | None = None,
    *,
    manager: PathManager = _manager,
    **get_local_path_kwargs: T.Any,
) -> _PathCallable | T.Callable[[_PathCallable], _PathCallable]:
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


#################################
# Exported methods from manager #
#################################


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
