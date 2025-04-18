import random
from dataclasses import dataclass

from game import Event, Mod, Source, Stat, Stats, Unit, WeakAction, trigger
from game.stats import *

from ..flags import DamageFlag
from ..multipier import Calculator, Multipier, clamp


@dataclass
class EventDamage(Event):
    damage: "Damage"


@dataclass
class EventDeath(Event):
    node: "DeathNode"


class DeathNode(WeakAction):
    def __init__(self, source: Source | None, unit: Unit, priority=0) -> None:
        super().__init__("Dead", unit, priority)
        self.source = source
        self._keep_ref = source

    def run(self):
        self.unit.status[Alive] = False
        trigger(EventDeath(self))
        self._keep_ref = None


class DeathProtection(Mod):
    def protect(self, source: Source | None): ...


class Damage(Calculator, Source):
    def __init__(
        self,
        source: Source | None,
        unit: Unit,
        target: Unit,
        scale: float,
        flag: DamageFlag,
        element: ElementFlag,
        stat_type: type[Stat[float]] = ATK,
    ) -> None:
        super().__init__()
        Source.__init__(self, source)
        self.unit = unit
        self.target = target
        self.source_stats = Stats()
        self.target_stats = Stats()
        self.source_stats += self.unit.stats
        self.target_stats += self.target.stats
        self.scale = scale
        self.flag = flag
        self.element = element
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
        with self.source_stats.temp(flag=self.flag | self.element):
            with self.target_stats.temp(flag=self.flag | self.element):
                return super().calc()

    def deal(self):
        trigger(EventDamage(self))
        amount = self.calc()
        self.target.status[HP, self] -= amount
        if self.target.status[HP] <= 0.0:
            protection = self.target.get_mod(DeathProtection)
            if protection is not None:
                protection.protect(self)
            else:
                DeathNode(self, self.target).chain()


class BaseDamageMultipier(Multipier[Damage]):
    def get(self):
        return self.calculator.scale * self.calculator.source_stats.get(self.calculator.stat_type)


class CritMultipier(Multipier[Damage]):
    def __init__(self, calculator: Damage):
        super().__init__(calculator)
        self.rng = random.random()

    def is_crit(self):
        return self.rng < self.calculator.source_stats.get(CRIT_Rate)

    def get(self):
        return 1.0 + self.calculator.source_stats.get(CRIT_DMG) if self.is_crit() else 1.0


class DamageBoostMultipier(Multipier[Damage]):
    def get(self):
        return 1.0 + self.calculator.source_stats.get(DMG_Boost)


class WeakenMultipier(Multipier[Damage]):
    def get(self):
        return clamp(1.0 - self.calculator.source_stats.get(Weaken), 0.0, 1.0)


class DefenseMultipier(Multipier[Damage]):
    def get(self):
        with self.calculator.target_stats.temp(Stats(DEF(decrease=self.calculator.source_stats.get(DEF_Ignore)))):
            return (self.calculator.source_stats.get(Level) * 10.0 + 200.0) / (
                self.calculator.source_stats.get(Level) * 10.0 + 200.0 + max(0.0, self.calculator.target_stats.get(DEF))
            )


class ResistanceMultipier(Multipier[Damage]):
    def get(self):
        return clamp(1.0 - self.calculator.target_stats.get(DMG_RES) + self.calculator.source_stats.get(RES_PEN), 0.0, 2.0)


class VulnerabilityMultipier(Multipier[Damage]):
    def get(self):
        return 1.0 + self.calculator.target_stats.get(Vulnerability)


class DMGMitigationMultipier(Multipier[Damage]):
    def get(self):
        return max(1.0 - self.calculator.target_stats.get(DMG_Mitigation), 0.0)


class BrokenMultipier(Multipier[Damage]):
    def __init__(self, calculator: Damage):
        super().__init__(calculator)
        self.value = 1.0 if self.calculator.target.status[Toughness] <= 0.0 else 0.9

    def get(self):
        return self.value
