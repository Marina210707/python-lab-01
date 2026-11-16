from dataclasses import dataclass

@dataclass(frozen=True)
class Posting:
    __slots__ = ('doc_id', 'freq')
    doc_id: int
    freq: int

    def __getstate__(self) -> tuple[int, int]:
        return (self.doc_id, self.freq)

    def __setstate__(self, state: tuple[int, int]) -> None:
        object.__setattr__(self, 'doc_id', state[0])
        object.__setattr__(self, 'freq', state[1])

@dataclass(frozen=True)
class DocMeta:
    __slots__ = ('doc_id', 'title', 'length')
    doc_id: int
    title: str
    length: int

    def __getstate__(self) -> tuple[int, str, int]:
        return (self.doc_id, self.title, self.length)

    def __setstate__(self, state: tuple[int, str, int]) -> None:
        object.__setattr__(self, 'doc_id', state[0])
        object.__setattr__(self, 'title', state[1])
        object.__setattr__(self, 'length', state[2])