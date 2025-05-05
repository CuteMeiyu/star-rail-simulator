from dataclasses import dataclass

from game import Event, FlexFlag, MixFlag, Source, Unit, UnitNode, WeakAction, listen, trigger
from game.conditions import BrokenCondition
from game.events import EventTurn
from game.stats import *

from ...multipier import Multipier, SourceTargetCalculator
from ...priority import Priority


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


class ToughnessDamage(SourceTargetCalculator, Source):
    def __init__(self, source: Source | None, source_unit: Unit, target_unit: Unit, amount: float, flag: None | FlexFlag | MixFlag, *multipiers: Multipier) -> None:
        super().__init__(source_unit, target_unit, flag, *multipiers)
        Source.__init__(self, source)
        self.base_amount = amount
        self.add_multipiers(
            BaseToughnessMultipier(),
            BreakEfficiencyMultipier(),
            WeaknessMultipier(),
        )

    def deal(self):
        trigger(EventToughnessDamage(self))
        amount = self.calc()
        if amount <= 0:
            return
        self.target_unit.status[Toughness, self] -= amount


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
        if calculator.target_stats.get_stat(Weakness).has_intersection(calculator.flag):
            return 1.0
        return min(calculator.source_stats.get(WeaknessIgnore), 1.0)


def _on_turn(event: EventTurn):
    if not event.unit.status[Broken]:
        return
    WeaknessRestoreNode(event.unit).chain()


listen(EventTurn, _on_turn, Priority.Event.weakness_restore)
