from hsr.characters.rmc import Mem, MemsSupport

from ..console import ModSuffix, Suffix

ModSuffix.table[MemsSupport] = "♥"


class MemEnergySuffix(Suffix):
    def string(self) -> str:
        assert isinstance(self.unit, Mem)
        return str(int(self.unit.energy * 100))


def init(mem: Mem):
    MemEnergySuffix(mem).add()
