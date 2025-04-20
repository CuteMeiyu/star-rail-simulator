from game import Source, Unit
from game.stats import *

from ..buff import TickType
from ..data import common as data
from ..multipier import Multipier
from ..statusmanager import Damage, DamageFlag
from ..units import Enemy
from .breaking import BreakEffectMultipier
from .dot import DoTDebuff


class MaxHPPercentMultipier(Multipier[Damage]):
    def __init__(self, percent: float) -> None:
        super().__init__()
        self.percent = percent

    def get(self, calculator) -> float:
        return self.percent * calculator.target_stats[HP]


class Bleed(DoTDebuff):
    def __init__(self, source: Source | None, source_unit: Unit, target_unit: Unit, duration: int, base_chance: float, fixed_chance: float, *multipiers: Multipier) -> None:
        super().__init__(source, "Bleed", source_unit, target_unit, duration, TickType.start_end, DebuffFlag.bleed, base_chance, fixed_chance, DamageFlag.dot, ElementFlag.physical, *multipiers)


class BreakBleed(Bleed):
    def __init__(self, source_unit: Unit, target_unit: Unit) -> None:
        hp_percent = data.BreakExtraMultipier.physical_elite if isinstance(target_unit, Enemy) and target_unit.elite else data.BreakExtraMultipier.physical
        super().__init__(source_unit, source_unit, target_unit, 2, 1.5, 0.0, MaxHPPercentMultipier(hp_percent), BreakEffectMultipier())
