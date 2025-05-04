import random
from dataclasses import dataclass

from game import Event, Source, Stat, Stats, Unit, trigger
from game.stats import *

from ...multipier import Calculator, Multipier, clamp
from ..flags import DamageFlag, HealFlag


@dataclass
class EventDamage(Event):
    damage: "Damage"


@dataclass
class EventHeal(Event):
    heal: "Heal"


class Damage(Calculator, Source):
    def __init__(self, source: Source | None, unit: Unit, target: Unit, flag: DamageFlag, element: ElementFlag, *multipiers: Multipier) -> None:
        super().__init__()
        Source.__init__(self, source)
        self.unit = unit
        self.target = target
        self.source_stats = Stats()
        self.target_stats = Stats()
        self.source_stats += self.unit.stats
        self.target_stats += self.target.stats
        self.flag = flag
        self.element = element
        self.add_multipiers(
            *multipiers,
            DefenseMultipier(),
            ResistanceMultipier(),
            VulnerabilityMultipier(),
            DMGMitigationMultipier(),
            BrokenMultipier(self.target),
        )

    def calc(self):
        with self.source_stats.temp(flag=self.flag | self.element):
            with self.target_stats.temp(flag=self.flag | self.element):
                return super().calc()

    def deal(self):
        trigger(EventDamage(self))
        amount = self.calc()
        if amount <= 0:
            return
        self.target.status[HP, self] -= amount


class BaseDamageMultipier(Multipier[Damage]):
    def __init__(self, scale: float, stat_type: type[Stat] = ATK) -> None:
        super().__init__()
        self.scale = scale
        self.stat_type = stat_type

    def get(self, calculator):
        return self.scale * calculator.source_stats.get(self.stat_type)


class CritMultipier(Multipier[Damage]):
    def __init__(self):
        self.rng = random.random()
        self.crit = False
        """The last calculated result since `get()` called"""

    def get(self, calculator):
        if self.rng < calculator.source_stats.get(CRIT_Rate):
            self.crit = True
        else:
            self.crit = False
        return 1.0 + calculator.source_stats.get(CRIT_DMG) if self.crit else 1.0


class DamageBoostMultipier(Multipier[Damage]):
    def get(self, calculator):
        return 1.0 + calculator.source_stats.get(DMG_Boost)


class WeakenMultipier(Multipier[Damage]):
    def get(self, calculator):
        return clamp(1.0 - calculator.source_stats.get(Weaken), 0.0, 1.0)


class DefenseMultipier(Multipier[Damage]):
    def get(self, calculator):
        with calculator.target_stats.temp(Stats(DEF(decrease=calculator.source_stats.get(DEF_Ignore)))):
            return (calculator.source_stats.get(Level) * 10.0 + 200.0) / (calculator.source_stats.get(Level) * 10.0 + 200.0 + max(0.0, calculator.target_stats.get(DEF)))


class ResistanceMultipier(Multipier[Damage]):
    def get(self, calculator):
        return clamp(1.0 - calculator.target_stats.get(DMG_RES) + calculator.source_stats.get(RES_PEN), 0.0, 2.0)


class VulnerabilityMultipier(Multipier[Damage]):
    def get(self, calculator):
        return 1.0 + calculator.target_stats.get(Vulnerability)


class DMGMitigationMultipier(Multipier[Damage]):
    def get(self, calculator):
        return max(1.0 - calculator.target_stats.get(DMG_Mitigation), 0.0)


class BrokenMultipier(Multipier[Damage]):
    def __init__(self, target: Unit):
        super().__init__()
        self.value = 0.9 if target.status[Toughness] > 0 else 1.0

    def get(self, calculator):
        return self.value


class Heal(Calculator, Source):
    def __init__(self, source: Source | None, unit: Unit, target: Unit, flag: HealFlag, *multipiers: Multipier) -> None:
        super().__init__()
        Source.__init__(self, source)
        self.unit = unit
        self.target = target
        self.source_stats = Stats()
        self.target_stats = Stats()
        self.source_stats += self.unit.stats
        self.target_stats += self.target.stats
        self.flag = flag
        self.add_multipiers(
            *multipiers,
            OutgoingHealingBoostMultipier(),
        )

    def calc(self):
        with self.source_stats.temp(flag=self.flag):
            with self.target_stats.temp(flag=self.flag):
                return super().calc()

    def deal(self):
        trigger(EventHeal(self))
        amount = self.calc()
        if amount <= 0:
            return
        self.target.status[HP, self] += amount


class OutgoingHealingBoostMultipier(Multipier[Heal]):
    def get(self, calculator: Heal) -> float:
        return 1.0 + calculator.source_stats[Outgoing_Healing_Boost]


class TrueDamage(Damage):
    def __init__(self, source: Source | None, unit: Unit, target: Unit, amount: float) -> None:
        super().__init__(source, unit, target, DamageFlag(), element=ElementFlag())
        self.clear_multipier()
        self.add_multipier(FixedAmountMultipier(amount))


class FixedAmountMultipier(Multipier):
    def __init__(self, amount: float) -> None:
        super().__init__()
        self.amount = amount

    def get(self, calculator) -> float:
        return self.amount
