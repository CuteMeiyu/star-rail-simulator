from .flags import DamageFlag
from .multipier import Multipier
from .shortcuts import deal_damage, regenerate_energy
from .status import energy, hp, toughness
from .status.energy import EnergyRegenerate
from .status.hp import Damage
from .status.toughness import ToughnessDamage
from .statuscap import disable_status_cap, enable_status_cap

enable_status_cap()
