from game import FlexFlag, MixFlag, Source, Unit
from game.stats import ATK, Stat

from .multipiers import BaseDamageMultipier, CritMultipier, DamageBoostMultipier, WeakenMultipier
from .status.energy import EnergyRegenerate
from .status.hp import Damage
from .status.toughness import ToughnessDamage


def deal_damage(source: Source | None, source_unit: Unit, target_unit: Unit, scale: float, toughness: float, flag: FlexFlag | MixFlag, stat_type: type[Stat[float]] = ATK):
    damage = Damage(source, source_unit, target_unit, flag, BaseDamageMultipier(scale, stat_type), CritMultipier(), DamageBoostMultipier(), WeakenMultipier())
    toughness_damage = ToughnessDamage(source, source_unit, target_unit, toughness, flag)
    toughness_damage.deal()
    damage.deal()


def regenerate_energy(source: Source | None, unit: Unit, amount: float, apply_regeneration_rate: bool):
    EnergyRegenerate(source, unit, amount, apply_regeneration_rate).deal()
