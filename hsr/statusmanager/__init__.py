from .flags import DamageFlag, HealFlag
from .shortcuts import deal_damage, regenerate_energy
from .status import energy, hp, toughness
from .status.energy import EnergyRegenerate
from .status.hp import Damage, Heal, TrueDamage
from .status.toughness import ToughnessDamage, WeaknessRestore
from .statuscap import BreakProtection, Death, DeathProtection

__all__ = [
    "Damage",
    "TrueDamage",
    "Heal",
    "EnergyRegenerate",
    "ToughnessDamage",
    "WeaknessRestore",
    "BreakProtection",
    "Death",
    "DeathProtection",
    "deal_damage",
    "regenerate_energy",
    "DamageFlag",
    "HealFlag",
    "energy",
    "hp",
    "toughness",
]
