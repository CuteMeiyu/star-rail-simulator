from dataclasses import dataclass

from game import Event, Source, Stats, Unit, trigger
from game.stats import *

from ..flags import DamageFlag
from ..multipier import Calculator, Multipier


@dataclass
class EventToughnessDamage(Event):
    damage: "ToughnessDamage"


class ToughnessDamage(Calculator, Source):
    def __init__(self, source: Source | None, unit: Unit, target: Unit, amount: float, flag: DamageFlag, element: ElementFlag) -> None:
        super().__init__()
        Source.__init__(self, source)
        self.unit = unit
        self.target = target
        self.source_stats = Stats()
        self.target_stats = Stats()
        self.source_stats += self.unit.stats
        self.target_stats += self.target.stats
        self.base_amount = amount
        self.flag = flag
        self.element = element
        self.add_multipiers(
            BaseToughnessMultipier(self),
            BreakEfficiencyMultipier(self),
            WeaknessMultipier(self),
        )

    def calc(self):
        with self.source_stats.temp(flag=self.flag | self.element):
            with self.target_stats.temp(flag=self.flag | self.element):
                return super().calc()

    def deal(self):
        trigger(EventToughnessDamage(self))
        amount = self.calc()
        self.target.status[Toughness, self] -= amount
        if self.target.status[Toughness] <= 0.0:
            pass


class BaseToughnessMultipier(Multipier[ToughnessDamage]):
    def get(self):
        return self.calculator.base_amount


class BreakEfficiencyMultipier(Multipier[ToughnessDamage]):
    def get(self):
        return 1.0 + self.calculator.source_stats.get(Break_Efficiency)


class WeaknessMultipier(Multipier[ToughnessDamage]):
    def get(self):
        if self.calculator.target_stats.get(WeaknessProtection) > 0:
            return 0.0
        if self.calculator.target_stats.get_stat(Weakness).has_intersection(self.calculator.element):
            return 1.0
        return min(self.calculator.source_stats.get(WeaknessIgnore), 1.0)
