import os
from pathlib import Path

import wandb

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


def test_wandb_artifact():
    wandb.use_artifact(
        "wandb-artifact:///tue-mps/multidvps/run-multidvps-cityscapes-resnet50-2023-12-05T10-05-52-step-5000:6225cf14e76d63ce43ea/model.safetensors"
    )
