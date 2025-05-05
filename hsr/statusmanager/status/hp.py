import random
from dataclasses import dataclass

from game import Event, FlexFlag, MixFlag, Source, Stat, Stats, Unit, trigger
from game.stats import *

from ...multipier import Multipier, SourceTargetCalculator, clamp


@dataclass
class EventDamage(Event):
    damage: "Damage"


@dataclass
class EventHeal(Event):
    heal: "Heal"


class Damage(SourceTargetCalculator, Source):
    def __init__(self, source: Source | None, source_unit: Unit, target_unit: Unit, flag: None | FlexFlag | MixFlag, *multipiers: Multipier) -> None:
        super().__init__(source_unit, target_unit, flag, *multipiers)
        Source.__init__(self, source)
        self.add_multipiers(
            DefenseMultipier(),
            ResistanceMultipier(),
            VulnerabilityMultipier(),
            DMGMitigationMultipier(),
            BrokenMultipier(self.target_unit),
        )

    def deal(self):
        trigger(EventDamage(self))
        amount = self.calc()
        if amount <= 0:
            return
        self.target_unit.status[HP, self] -= amount


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


class Heal(SourceTargetCalculator, Source):
    def __init__(self, source: Source | None, unit: Unit, target: Unit, flag: None | FlexFlag | MixFlag, *multipiers: Multipier) -> None:
        super().__init__(unit, target, flag, *multipiers)
        Source.__init__(self, source)
        self.add_multipiers(
            OutgoingHealingBoostMultipier(),
        )

    def deal(self):
        trigger(EventHeal(self))
        amount = self.calc()
        if amount <= 0:
            return
        self.target_unit.status[HP, self] += amount


class OutgoingHealingBoostMultipier(Multipier[Heal]):
    def get(self, calculator: Heal) -> float:
        return 1.0 + calculator.source_stats[Outgoing_Healing_Boost]


class TrueDamage(Damage):
    def __init__(self, source: Source | None, source_unit: Unit, target_unit: Unit, amount: float, flag: None | FlexFlag | MixFlag) -> None:
        super().__init__(source, source_unit, target_unit, flag)
        self.clear_multipier()
        self.add_multipier(LiteralAmountMultipier(amount))


class LiteralAmountMultipier(Multipier):
    def __init__(self, amount: float) -> None:
        super().__init__()
        self.amount = amount

    def get(self, calculator) -> float:
        return self.amount
