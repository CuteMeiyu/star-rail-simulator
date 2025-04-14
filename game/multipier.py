import math
import random
from dataclasses import dataclass
from typing import Generic, TypeVar
from weakref import ref

from game.stats import Stats

from .combat import Unit
from .event import Event, trigger
from .flexflag import FlexFlag
from .source import Source
from .stats import *


@dataclass
class EventDamage(Event):
    damage: "Damage"


def clamp(value: float, lower_bound: float, upper_bound: float):
    return min(max(lower_bound, value), upper_bound)


_T_Calculator = TypeVar("_T_Calculator", bound="Calculator")


class Multipier(Generic[_T_Calculator]):
    def __init__(self, calculator: _T_Calculator):
        self._calculator_ref = ref(calculator)

    @property
    def calculator(self) -> _T_Calculator:
        calculator = self._calculator_ref()
        assert calculator is not None
        return calculator

    def get(self) -> float:
        return 1.0


_T_Multipier = TypeVar("_T_Multipier", bound=Multipier)


class Calculator:
    def __init__(self) -> None:
        self.multipiers: list[Multipier] = []

    def get_multipier(self, multipier_cls: type[_T_Multipier]) -> _T_Multipier | None:
        for multipier in self.multipiers:
            if isinstance(multipier, multipier_cls):
                return multipier
        return None

    def add_multipier(self, multipier: Multipier):
        assert self.get_multipier(type(multipier)) is None
        self.multipiers.append(multipier)

    def add_multipiers(self, *multipiers: Multipier):
        for multipier in multipiers:
            self.add_multipier(multipier)

    def remove_multipier(self, multipier: Multipier):
        self.multipiers.remove(multipier)

    def update_multipier(self, multipier: Multipier):
        old_multipier = self.get_multipier(type(multipier))
        assert old_multipier is not None
        self.remove_multipier(old_multipier)
        self.add_multipier(multipier)

    def calc(self):
        return math.prod(multipier.get() for multipier in self.multipiers)


class DamageFlag(FlexFlag):
    basic: "DamageFlag"
    skill: "DamageFlag"
    ult: "DamageFlag"
    dot: "DamageFlag"
    follow_up: "DamageFlag"
    counter: "DamageFlag"
    additional: "DamageFlag"
    breaking: "DamageFlag"
    super_break: "DamageFlag"


DamageFlag.counter |= DamageFlag.follow_up
DamageFlag.super_break |= DamageFlag.breaking


class DamageCalculator(Calculator):
    def __init__(
        self,
        unit: Unit,
        target: Unit,
        scale: float,
        flag: DamageFlag,
        combat_type: CombatType,
        stat_type: type[Stat[float]] = ATK,
    ) -> None:
        super().__init__()
        self.unit = unit
        self.target = target
        self.source_stats = Stats()
        self.target_stats = Stats()
        self.source_stats += self.unit.stats
        self.target_stats += self.target.stats
        self.scale = scale
        self.flag = flag
        self.combat_type = combat_type
        self.stat_type = stat_type
        self.add_multipiers(
            BaseDamageMultipier(self),
            CritMultipier(self),
            DamageBoostMultipier(self),
            WeakenMultipier(self),
            DefenseMultipier(self),
            ResistanceMultipier(self),
            VulnerabilityMultipier(self),
            DMGMitigationMultipier(self),
            BrokenMultipier(self),
        )

    def calc(self):
        with self.source_stats.temp(flag=self.flag):
            with self.target_stats.temp(flag=self.flag):
                return super().calc()


class BaseDamageMultipier(Multipier[DamageCalculator]):
    def get(self):
        return self.calculator.scale * self.calculator.source_stats.get(self.calculator.stat_type)


class CritMultipier(Multipier[DamageCalculator]):
    def __init__(self, calculator: DamageCalculator):
        super().__init__(calculator)
        self.rng = random.random()

    def is_crit(self):
        return self.rng < self.calculator.source_stats.get(CRIT_Rate)

    def get(self):
        return 1.0 + self.calculator.source_stats.get(CRIT_DMG) if self.is_crit() else 1.0


class DamageBoostMultipier(Multipier[DamageCalculator]):
    def get(self):
        return 1.0 + self.calculator.source_stats.get(DMG_Boost)


class WeakenMultipier(Multipier[DamageCalculator]):
    def get(self):
        return clamp(1.0 - self.calculator.source_stats.get(Weaken), 0.0, 1.0)


class DefenseMultipier(Multipier[DamageCalculator]):
    def get(self):
        with self.calculator.target_stats.temp(Stats(DEF(decrease=self.calculator.source_stats.get(DEF_Ignore)))):
            return (self.calculator.source_stats.get(Level) * 10.0 + 200.0) / (
                self.calculator.source_stats.get(Level) * 10.0 + 200.0 + max(0.0, self.calculator.target_stats.get(DEF))
            )


class ResistanceMultipier(Multipier[DamageCalculator]):
    def get(self):
        return clamp(1.0 - self.calculator.target_stats.get(DMG_RES) + self.calculator.source_stats.get(RES_PEN), 0.0, 2.0)


class VulnerabilityMultipier(Multipier[DamageCalculator]):
    def get(self):
        return 1.0 + self.calculator.target_stats.get(Vulnerability)


class DMGMitigationMultipier(Multipier[DamageCalculator]):
    def get(self):
        return max(1.0 - self.calculator.target_stats.get(DMG_Mitigation), 0.0)


class BrokenMultipier(Multipier[DamageCalculator]):
    def __init__(self, calculator: DamageCalculator):
        super().__init__(calculator)
        self.value = 1.0 if self.calculator.target.status.toughness <= 0.0 else 0.9

    def get(self):
        return self.value


class ToughnessCalculator(Calculator):
    def __init__(self, unit: Unit, target: Unit, amount: float, flag: DamageFlag, combat_type: CombatType) -> None:
        super().__init__()
        self.unit = unit
        self.target = target
        self.source_stats = Stats()
        self.target_stats = Stats()
        self.source_stats += self.unit.stats
        self.target_stats += self.target.stats
        self.base_amount = amount
        self.flag = flag
        self.combat_type = combat_type
        self.add_multipiers(
            BaseToughnessMultipier(self),
            BreakEfficiencyMultipier(self),
            WeaknessMultipier(self),
        )

    def calc(self):
        with self.source_stats.temp(flag=self.flag):
            with self.target_stats.temp(flag=self.flag):
                return super().calc()


class BaseToughnessMultipier(Multipier[ToughnessCalculator]):
    def get(self):
        return self.calculator.base_amount


class BreakEfficiencyMultipier(Multipier[ToughnessCalculator]):
    def get(self):
        return 1.0 + self.calculator.source_stats.get(Break_Efficiency)


class WeaknessMultipier(Multipier[ToughnessCalculator]):
    def get(self):
        if self.calculator.target_stats.get(WeaknessProtection) > 0:
            return 0.0
        if self.calculator.combat_type in self.calculator.target_stats.get(Weakness):
            return 1.0
        return min(self.calculator.source_stats.get(WeaknessIgnore), 1.0)


class Damage(Source):
    def __init__(
        self,
        source: Source | None,
        unit: Unit,
        target: Unit,
        scale: float,
        toughness: float,
        flag: DamageFlag,
        combat_type: CombatType,
        stat_type: type[Stat[float]] = ATK,
    ) -> None:
        super().__init__(source)
        self.damage_calculator = DamageCalculator(unit, target, scale, flag, combat_type, stat_type)
        self.toughness_calculator = ToughnessCalculator(unit, target, toughness, flag, combat_type)

    def deal(self):
        trigger(EventDamage(self))
        toughness_amount = self.toughness_calculator.calc()
        self.toughness_calculator.target.change_toughness(self, -toughness_amount)
        damage_amount = self.damage_calculator.calc()
        self.damage_calculator.target.change_hp(self, -damage_amount)
