import os
from multiprocessing import RLock
from pathlib import Path

import pytest
import wandb

from unicore import file_io

WANDB_LOCK = RLock()


@pytest.fixture()
def wandb_run(tmp_path):
    os.environ["WANDB_MODE"] = "dryrun"
    os.environ["WANDB_DIR"] = str(tmp_path)
    os.environ["WANDB_API_KEY"] = "test"

    with WANDB_LOCK:
        if wandb.run is None:
            wandb.init(project="test", entity="test")
    yield wandb.run
    # wandb.finish()


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


@pytest.mark.parametrize(
    "path",
    [
        "wandb-artifact://test/artifact/name:version",
        "wandb-artifact://test/artifact/name:version/",
        "wandb-artifact://test/artifact/name:version/path/to/file",
        "wandb-artifact:///test/artifact/name:version/path/to/file",
    ],
)
def test_wandb_artifact(wandb_run, path):
    with pytest.raises(FileNotFoundError):
        file_io.get_local_path(path)
