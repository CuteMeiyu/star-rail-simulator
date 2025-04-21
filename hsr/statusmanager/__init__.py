from .flags import DamageFlag
from .shortcuts import deal_damage, regenerate_energy
from .status import energy, hp, toughness
from .status.energy import EnergyRegenerate
from .status.hp import Damage
from .status.toughness import ToughnessDamage, WeaknessRestore
from .statuscap import BreakProtection, Death, DeathProtection
