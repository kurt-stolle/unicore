# from typing import List
# from iopath.common.file_io import PathHandler
# from unicore.utils.prototypes.iopathlib import PureIoPath, IoPath, Path
# from typing_extensions import override
# import pytest
# import urllib.error


# @pytest.fixture()
# def mock_handler(tmpdir: Path):
#     from iopath.common.file_io import PathHandler

#     class MockHandler(PathHandler):
#         def __init__(self, tmpdir: Path, **kwargs):
#             super().__init__(**kwargs)
#             self.mock_dir = tmpdir

#         @override
#         def _get_supported_prefixes(self) -> List[str]:
#             return ["mock://", "//mock/", "///////"]

#         @override
#         def _get_local_path(self, path, **kwargs):
#             return self.mock_dir + path[6:]

#         @override
#         def _open(self, path, mode="r", **kwargs):
#             return open(self._get_local_path(path), mode, **kwargs)

#     return MockHandler(tmpdir)


# @pytest.fixture()
# def path_manager(request, mock_handler: PathHandler):
#     from iopath.common.file_io import PathManagerFactory, HTTPURLHandler, PathHandler

#     pm = PathManagerFactory.get(defaults_setup=False)
#     pm.register_handler(HTTPURLHandler(), allow_override=True)
#     pm.register_handler(mock_handler, allow_override=True)
#     return pm


# def test_pure_iopath():
#     path = PureIoPath(__file__)

#     assert isinstance(path, PureIoPath)
#     assert Path(path) == Path(__file__)


# def test_managed_iopath(path_manager, mock_handler):
#     class ManagedIoPath(IoPath, manager=path_manager):
#         pass

#     test_txt = mock_handler.mock_dir / "test.txt"
#     test_txt.write_text("foo", encoding="utf-8")

#     # Test with single path
#     path = ManagedIoPath("tests/utils/test_iopathlib.py")
#     assert isinstance(path, ManagedIoPath)
#     assert path.exists()
#     assert path.is_file()

#     # Test with dual paths
#     path = ManagedIoPath("tests/utils/test_iopathlib.py", "tests/utils/test_pathlib.py")

#     assert isinstance(path, ManagedIoPath)
#     assert not path.exists()

#     # Test with a defined prefix
#     for prefix in mock_handler._get_supported_prefixes():
#         # Valid prefix
#         path = ManagedIoPath(f"{prefix}test.txt")
#         assert isinstance(path, ManagedIoPath)
#         assert path.exists()
#         assert path.is_file()
#         assert path.read_text() == "foo"

#         # Invalid prefix
#         path = ManagedIoPath("mock/test.txt")
#         assert path.drive == ""

#         assert isinstance(path, ManagedIoPath)
#         assert not path.exists()
#         assert not path.is_file()

#     # Test with a URL
#     with pytest.raises(urllib.error.URLError):
#         ManagedIoPath("https://example.com/path/to/file.txt")
