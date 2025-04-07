from typing import TypeVar
from weakref import ref

T = TypeVar("T", bound="Source")


class Source:
    def __init__(self, source: "Source | None") -> None:
        self._source_ref = None if source is None else ref(source)

    @property
    def source(self) -> "Source | None":
        return self._source_ref() if self._source_ref is not None else None

    @source.setter
    def source(self, source: "Source | None"):
        self._source_ref = ref(source) if source is not None else None

    def get_source(self, source_class: type[T]):
        source = self
        while source is not None:
            if isinstance(source, source_class):
                return source
            source = source.source
        return None
