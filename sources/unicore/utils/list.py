from typing_extensions import override


def _frozen_method(self, *args, **kwargs):
    raise TypeError(f"'{type(self).__name__}' is frozen")


class frozenlist(list):
    def __init__(self, other):
        self._list = other

    @override
    def __getitem__(self, index):
        return self._list[index]

    @override
    def __iter__(self):
        return iter(self._list)

    def __slice__(self, *args, **kw):
        return self._list.__slice__(*args, **kw)

    @override
    def __repr__(self):
        return repr(self._list)

    @override
    def __len__(self):
        return len(self._list)

    append = pop = __setitem__ = __setslice__ = __delitem__ = _frozen_method
