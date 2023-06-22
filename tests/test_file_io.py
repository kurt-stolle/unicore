import os
from pathlib import Path

from unicore import file_io


def test_file_io_globals():
    for d in dir(file_io):
        assert getattr(file_io, d) is not None


def test_file_io_environ():
    path = file_io.get_local_path("//datasets/")
    assert path == str(Path(os.environ.get("UNICORE_DATASETS", "datasets")).resolve())

    path = file_io.get_local_path("//cache/")
    assert path == str(Path(os.environ.get("UNICORE_CACHE", "cache")).resolve())

    path = file_io.get_local_path("//output/")
    assert path == str(Path(os.environ.get("UNICORE_OUTPUT", "output")).resolve())
