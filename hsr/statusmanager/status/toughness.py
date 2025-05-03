from dataclasses import dataclass

from game import Event, Source, Stats, Unit, UnitNode, WeakAction, listen, trigger
from game.conditions import BrokenCondition
from game.events import EventTurn
from game.stats import *

from ...multipier import Calculator, Multipier
from ...priority import Priority
from ..flags import DamageFlag


@dataclass
class EventToughnessDamage(Event):
    damage: "ToughnessDamage"


@dataclass
class EventWeaknessRestore(Event):
    weakness_restore: "WeaknessRestore"


class WeaknessRestore(WeakAction):
    def __init__(self, unit: Unit, percent=1.0, priority=0) -> None:
        super().__init__("Weakness Restore", unit, priority)
        self.percent = percent
        self.remove_condition(BrokenCondition)

    def run(self):
        self.unit.status[Broken] = False
        self.unit.status[Toughness, self] = self.unit.stats[Toughness] * self.percent
        trigger(EventWeaknessRestore(self))


class WeaknessRestoreNode(UnitNode):
    def __init__(self, unit: Unit, percent=1.0, priority=0) -> None:
        super().__init__(unit, priority)
        self.percent = percent

    def run(self):
        WeaknessRestore(self.unit, self.percent, self.priority).chain(True)


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
            BaseToughnessMultipier(),
            BreakEfficiencyMultipier(),
            WeaknessMultipier(),
        )

    def calc(self):
        with self.source_stats.temp(flag=self.flag | self.element):
            with self.target_stats.temp(flag=self.flag | self.element):
                return super().calc()

    def deal(self):
        trigger(EventToughnessDamage(self))
        amount = self.calc()
        if amount <= 0:
            return
        self.target.status[Toughness, self] -= amount


class BaseToughnessMultipier(Multipier[ToughnessDamage]):
    def get(self, calculator):
        return calculator.base_amount


class BreakEfficiencyMultipier(Multipier[ToughnessDamage]):
    def get(self, calculator):
        return 1.0 + calculator.source_stats.get(Break_Efficiency)


class WeaknessMultipier(Multipier[ToughnessDamage]):
    def get(self, calculator):
        if calculator.target_stats.get(WeaknessProtection) > 0:
            return 0.0
        if calculator.target_stats.get_stat(Weakness).has_intersection(calculator.element):
            return 1.0
        return min(calculator.source_stats.get(WeaknessIgnore), 1.0)


def _on_turn(event: EventTurn):
    if not event.unit.status[Broken]:
        return
    WeaknessRestoreNode(event.unit).chain()


listen(EventTurn, _on_turn, Priority.Event.weakness_restore)
