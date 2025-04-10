import math
import random
from dataclasses import dataclass
from typing import Generic, TypeVar
from weakref import ref

from hsrgame.stats import Stats

from .combat import Unit
from .event import Event, trigger
from .flexflag import FlexFlag
from .source import Source
from .stats import *


def clamp(value: float, lower_bound: float, upper_bound: float):
    return min(max(lower_bound, value), upper_bound)


@dataclass
class EventDamage(Event):
    damage: "DamageBase"


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


_T_Damage = TypeVar("_T_Damage", bound="DamageBase")


class Multipier(Generic[_T_Damage]):
    def __init__(self, damage: _T_Damage):
        self._damage_ref = ref(damage)

    @property
    def damage(self):
        damage = self._damage_ref()
        assert damage is not None
        return damage

    def get(self) -> float:
        return 0.0


_T_Multipier = TypeVar("_T_Multipier", bound=Multipier)


class CritMultipier(Multipier):
    def __init__(self, damage: "DamageBase"):
        super().__init__(damage)
        self.rng = random.random()

    def is_crit(self):
        return self.rng < self.damage.source_stats.get(CRIT_Rate)

    def get(self):
        return 1.0 + self.damage.source_stats.get(CRIT_DMG) if self.is_crit() else 1.0


class DamageBoostMultipier(Multipier):
    def get(self):
        return 1.0 + self.damage.source_stats.get(DMG_Boost)


class WeakenMultipier(Multipier):
    def get(self):
        return clamp(1.0 - self.damage.source_stats.get(Weaken), 0.0, 1.0)


class DefenseMultipier(Multipier):
    def get(self):
        with self.damage.target_stats.temp(Stats(DEF(decrease=self.damage.source_stats.get(DEF_Ignore)))):
            return (self.damage.source_stats.get(Level) * 10.0 + 200.0) / (
                self.damage.source_stats.get(Level) * 10.0 + 200.0 + max(0.0, self.damage.target_stats.get(DEF))
            )


class ResistanceMultipier(Multipier):
    def get(self):
        return clamp(1.0 - self.damage.target_stats.get(DMG_RES) + self.damage.source_stats.get(RES_PEN), 0.0, 2.0)


class VulnerabilityMultipier(Multipier):
    def get(self):
        return 1.0 + self.damage.target_stats.get(Vulnerability)


class DMGMitigationMultipier(Multipier):
    def get(self):
        return max(1.0 - self.damage.target_stats.get(DMG_Mitigation), 0.0)


class BrokenMultipier(Multipier):
    def get(self):
        return 1.0 if self.damage.target.status.toughness <= 0.0 else 0.9


class DamageBase(Source):
    def __init__(self, source: Source | None, unit: Unit, target: Unit) -> None:
        super().__init__(source)
        self.unit = unit
        self.target = target
        self.source_stats = Stats()
        self.target_stats = Stats()
        self.source_stats += self.unit.stats
        self.target_stats += self.target.stats
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

    def deal(self):
        trigger(EventDamage(self))


class BaseDamageMultipier(Multipier["Damage"]):
    def get(self):
        return self.damage.scale * self.damage.source_stats.get(self.damage.stat_type)


class Damage(DamageBase):
    def __init__(
        self,
        source: Source | None,
        unit: Unit,
        target: Unit,
        scale: float,
        flag: DamageFlag,
        combat_type: CombatType,
        stat_type: type[Stat[float]] = ATK,
    ) -> None:
        super().__init__(source, unit, target)
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


class BaseToughnessDamageMultipier(Multipier["ToughnessDamage"]):
    def get(self):
        return self.damage.base_amount


class BreakEfficiencyMultipier(Multipier):
    def get(self):
        return 1.0 + self.damage.source_stats.get(Break_Efficiency)


class WeaknessMultipier(Multipier["ToughnessDamage"]):
    def get(self):
        if self.damage.target_stats.get(WeaknessProtect) > 0:
            return 0.0
        if self.damage.combat_type in self.damage.target_stats.get(Weakness):
            return 1.0
        return min(self.damage.source_stats.get(WeaknessIgnore), 1.0)


class ToughnessDamage(DamageBase):
    def __init__(self, source: Source | None, unit: Unit, target: Unit, amount: float, combat_type: CombatType, update_broken_status=False) -> None:
        super().__init__(source, unit, target)
        self.base_amount = amount
        self.combat_type = combat_type
        self.update_broken_status = update_broken_status
        self.add_multipiers(
            BaseToughnessDamageMultipier(self),
            BreakEfficiencyMultipier(self),
            WeaknessMultipier(self),
        )
