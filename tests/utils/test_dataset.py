import pytest
from typing_extensions import override

from unicore.utils.dataset import Dataset
from unicore.utils.frozendict import frozendict


class MyDataset(Dataset, info=lambda: {"name": "FooBar"}):
    @override
    def _load_data(self, it, info):
        if it["id"] == 1:
            return it | {"name": "Foo"}
        elif it["id"] == 2:
            return it | {"name": "Bar"}
        else:
            return it | {"name": "Baz"}

    @override
    def _build_manifest(self):
        return {"items": [{"id": 1}, {"id": 2}]}

    @staticmethod
    def gatherer(manifest):
        for i, v in enumerate(manifest["items"]):
            yield str(i), v


@pytest.fixture
def dataset():
    ds = MyDataset(queue_fn=MyDataset.gatherer)
    return ds


def test_dataset(dataset):
    from typing import Iterable, Mapping

    # Manifest
    assert isinstance(dataset.manifest, Iterable)

    mfst = dict(dataset.manifest)

    assert len(mfst["items"]) == 2
    assert isinstance(mfst, Mapping)
    assert isinstance(mfst["items"], Iterable)
    assert mfst["items"] == [{"id": 1}, {"id": 2}]

    # Queue
    assert isinstance(dataset.queue, Iterable)

    # Datapipe
    assert isinstance(dataset.datapipe, Iterable)
    assert list(dict(dataset.datapipe).values()) == [{"id": 1, "name": "Foo"}, {"id": 2, "name": "Bar"}]
