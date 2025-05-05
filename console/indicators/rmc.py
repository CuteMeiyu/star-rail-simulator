import math

from game.combat import Unit
from hsr.characters.rmc import Mem, MemsSupport

from ..console import ModSuffix, NumericSuffix

ModSuffix.table[MemsSupport] = "♥"


class MemEnergySuffix(NumericSuffix):
    def __init__(self, unit: Unit, priority=0) -> None:
        super().__init__(unit, ".0f", priority)

    def get_value(self) -> float | int:
        assert isinstance(self.unit, Mem)
        return self.unit.energy * 100


def init(mem: Mem):
    MemEnergySuffix(mem).add()
