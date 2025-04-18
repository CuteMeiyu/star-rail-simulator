from game import Source, Unit
from game.stats import ATK, ElementFlag, Stat

from .flags import DamageFlag
from .status.energy import EnergyRegenerate
from .status.hp import Damage
from .status.toughness import ToughnessDamage


def deal_damage(
    source: Source | None, unit: Unit, target: Unit, scale: float, toughness: float, flag: DamageFlag, element: ElementFlag, stat_type: type[Stat[float]] = ATK
):
    damage = Damage(source, unit, target, scale, flag, element, stat_type)
    toughness_damage = ToughnessDamage(source, unit, target, toughness, flag, element)
    toughness_damage.deal()
    damage.deal()


def regenerate_energy(source: Source | None, unit: Unit, amount: float, apply_regeneration_rate: bool):
    EnergyRegenerate(source, unit, amount, apply_regeneration_rate).deal()
