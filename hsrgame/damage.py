import random
from dataclasses import dataclass
from typing import Any

from .combat import Unit
from .event import Event, trigger
from .flexflag import FlexFlag
from .source import Source
from .stats import *


def clamp(value: float, lower_bound: float, upper_bound: float):
    return min(max(lower_bound, value), upper_bound)


@dataclass
class EventDamage(Event):
    damage: "Damage"


class DamageFlag(FlexFlag):
    Basic: "DamageFlag"
    Skill: "DamageFlag"
    Ult: "DamageFlag"
    DoT: "DamageFlag"
    FUA: "DamageFlag"
    Counter: "DamageFlag"
    Additional: "DamageFlag"
    Break: "DamageFlag"
    SuperBreak: "DamageFlag"


DamageFlag.Counter |= DamageFlag.FUA
DamageFlag.SuperBreak |= DamageFlag.Break


class Damage(Source):
    def __init__(self, source: Source | None, unit: Unit, target: Unit, scale: float, flag: DamageFlag, stat_type: type[Stat[Any]] = ATK) -> None:
        super().__init__(source)
        self.unit = unit
        self.target = target
        self.scale = scale
        self.flag = flag
        self.stat_type = stat_type
        self.rng = random.random()
        self.source_stats = Stats()
        self.target_stats = Stats()
        self.source_stats += self.unit.stats
        self.target_stats += self.target.stats

    def is_crit(self):
        return self.rng < self.source_stats.get(CRIT_Rate)

    def get_base_damage(self) -> float:
        return self.scale * self.source_stats.get(self.stat_type)

    def get_crit_damage_multipier(self):
        return 1.0 + self.source_stats.get(CRIT_DMG) if self.is_crit() else 1.0

    def get_damage_boost_multipier(self):
        return 1.0 + self.source_stats.get(DMG_Boost)

    def get_weaken_multipier(self):
        return clamp(1.0 - self.source_stats.get(Weaken), 0.0, 1.0)

    def get_defense_multipier(self):
        with self.target_stats.temp(Stats(DEF(decrease=self.source_stats.get(DEF_Ignore)))):
            return (self.source_stats.get(Level) * 10.0 + 200.0) / (self.source_stats.get(Level) * 10.0 + 200.0 + max(0.0, self.target_stats.get(DEF)))

    def get_resistance_multipier(self):
        return clamp(1.0 - self.target_stats.get(DMG_RES) + self.source_stats.get(RES_PEN), 0.0, 2.0)

    def get_vulnerability_multipier(self):
        return 1.0 + self.target_stats.get(Vulnerability)

    def get_damage_mitigation_multipier(self):
        return max(1.0 - self.target_stats.get(DMG_Mitigation), 0.0)

    # def get_broken_multipier(self):
    #     return 1.0 if self.target.status.toughness <= 0.0 else 0.9

    def calc(self):
        return (
            self.get_base_damage()
            * self.get_crit_damage_multipier()
            * self.get_damage_boost_multipier()
            * self.get_weaken_multipier()
            * self.get_defense_multipier()
            * self.get_resistance_multipier()
            * self.get_vulnerability_multipier()
            * self.get_damage_mitigation_multipier()
            # * self.get_broken_multipier()
        )

    def deal(self):
        trigger(EventDamage(self))
        amount = self.calc()

        # for shield in self.target.get_mods(Shield):
        #     amount = shield.cost_hp(self, amount)
        #     if amount <= 0.0:
        #         break
        # if amount > 0.0:
        #     self.target.cost_hp(self, amount)
