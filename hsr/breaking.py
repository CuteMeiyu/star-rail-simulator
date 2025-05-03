from game import Unit, listen
from game.stats import *

from .buff import DebuffFlag
from .data import common as data
from .debuffs import DoTDebuff
from .debuffs import Entanglement as EntangleBase
from .debuffs import Frozen as FrozenBase
from .debuffs import Imprisonment as ImprisonBase
from .events import EventWeaknessBreak
from .multipier import Multipier
from .priority import Priority
from .statusmanager import Damage, DamageFlag, ToughnessDamage
from .units import Enemy


class MaxHPPercentMultipier(Multipier[Damage]):
    def __init__(self, percent: float) -> None:
        super().__init__()
        self.percent = percent

    def get(self, calculator) -> float:
        return self.percent * calculator.target_stats[HP]


class BaseBreakDamageMultipier(Multipier[Damage]):
    def __init__(self, scale: float) -> None:
        super().__init__()
        self.scale = scale

    def get(self, calculator: Damage) -> float:
        return data.break_base_damage[calculator.source_stats[Level] - 1] * self.scale


class BreakEffectMultipier(Multipier[Damage]):
    def get(self, calculator: Damage) -> float:
        return 1.0 + calculator.source_stats[Break_Effect]


class ToughnessMultipier(Multipier[Damage]):
    def get(self, calculator: Damage) -> float:
        return (calculator.target_stats[Toughness] + 20.0) * 0.025


class ImprisonmentScaleMultipier(Multipier):
    def __init__(self, scale: float) -> None:
        super().__init__()
        self.scale = scale

    def get(self, calculator: ImprisonBase) -> float:
        return self.scale


class BreakDoTDebuff(DoTDebuff):
    def __init__(self, name: str, source_unit: Unit, target_unit: Unit, debuff_flag: DebuffFlag, damage_type: ElementFlag, *multipiers: Multipier, max_stack=0) -> None:
        super().__init__(source_unit, name, source_unit, target_unit, 2, debuff_flag, 1.5, 0.0, DamageFlag.dot, damage_type, *multipiers, BreakEffectMultipier(), max_stack=max_stack)


class Bleed(BreakDoTDebuff):
    def __init__(self, source_unit: Unit, target_unit: Unit) -> None:
        super().__init__("Bleed", source_unit, target_unit, DebuffFlag.bleed, ElementFlag.physical)
        if isinstance(target_unit, Enemy) and target_unit.elite:
            self.add_multipier(MaxHPPercentMultipier(data.BreakExtraScale.physical_elite))
        else:
            self.add_multipier(MaxHPPercentMultipier(data.BreakExtraScale.physical))


class Burn(BreakDoTDebuff):
    def __init__(self, source_unit: Unit, target_unit: Unit) -> None:
        super().__init__("Burn", source_unit, target_unit, DebuffFlag.burn, ElementFlag.fire, BaseBreakDamageMultipier(data.BreakExtraScale.fire))


class Shock(BreakDoTDebuff):
    def __init__(self, source_unit: Unit, target_unit: Unit) -> None:
        super().__init__("Shock", source_unit, target_unit, DebuffFlag.shock, ElementFlag.lightning, BaseBreakDamageMultipier(data.BreakExtraScale.lightning))


class WindShear(BreakDoTDebuff):
    def __init__(self, source_unit: Unit, target_unit: Unit) -> None:
        super().__init__("Wind Shear", source_unit, target_unit, DebuffFlag.wind_shear, ElementFlag.wind, BaseBreakDamageMultipier(data.BreakExtraScale.wind), max_stack=3)
        if isinstance(target_unit, Enemy) and target_unit.elite:
            self.set_stacks(3)
        else:
            self.set_stacks(1)


class Frozen(FrozenBase):
    def __init__(self, source_unit: Unit, target_unit: Unit) -> None:
        super().__init__(source_unit, "Frozen", source_unit, target_unit, 1, 1.5, 0.0, BaseBreakDamageMultipier(data.BreakExtraScale.ice), BreakEffectMultipier())


class Entanglement(EntangleBase):
    def __init__(self, source_unit: Unit, target_unit: Unit) -> None:
        super().__init__(
            source_unit, "Entanglement", source_unit, target_unit, 1, 1.5, 0.0, BaseBreakDamageMultipier(data.BreakExtraScale.quantum_damage), BreakEffectMultipier(), ToughnessMultipier(), max_stack=5
        )


class Imprisonment(ImprisonBase):
    def __init__(self, source_unit: Unit, target_unit: Unit) -> None:
        super().__init__(self.unit, "Imprisonment", source_unit, target_unit, 1, 1.5, 0.0, speed_down=0.1)


def _deal_breaking_damage(source_unit: Unit, target_unit: Unit, element: ElementFlag, scale: float):
    Damage(source_unit, source_unit, target_unit, DamageFlag.breaking, element, BaseBreakDamageMultipier(scale), ToughnessMultipier(), BreakEffectMultipier()).deal()


def _on_weakness_break(event: EventWeaknessBreak):
    if event.source is None:
        return
    if isinstance(event.source, ToughnessDamage):
        source_unit = event.source.unit
        target_unit = event.source.target
        element = event.source.element
        source_stats = event.source.source_stats
    else:
        source_unit = event.source.get_source(Unit)
        if source_unit is None:
            return
        target_unit = event.unit
        element = getattr(event.source, "element", ElementFlag())
        source_stats = source_unit.stats
    if ElementFlag.fire in element:
        Burn(source_unit, target_unit).apply()
        _deal_breaking_damage(source_unit, target_unit, element, data.BreakScale.fire)
    elif ElementFlag.ice in element:
        Frozen(source_unit, target_unit).apply()
        _deal_breaking_damage(source_unit, target_unit, element, data.BreakScale.ice)
    elif ElementFlag.imaginary in element:
        target_unit.action_delay(data.BreakExtraScale.imaginary_delay * (1.0 + source_stats[Break_Effect]))
        Imprisonment(source_unit, target_unit).apply()
        _deal_breaking_damage(source_unit, target_unit, element, data.BreakScale.imaginary)
    elif ElementFlag.lightning in element:
        Shock(source_unit, target_unit).apply()
        _deal_breaking_damage(source_unit, target_unit, element, data.BreakScale.lightning)
    elif ElementFlag.physical in element:
        Bleed(source_unit, target_unit).apply()
        _deal_breaking_damage(source_unit, target_unit, element, data.BreakScale.physical)
    elif ElementFlag.quantum in element:
        target_unit.action_delay(data.BreakExtraScale.quantum_delay * (1.0 + source_stats[Break_Effect]))
        Entanglement(source_unit, target_unit).apply()
        _deal_breaking_damage(source_unit, target_unit, element, data.BreakScale.quantum)
    elif ElementFlag.wind in element:
        WindShear(source_unit, target_unit).apply()
        _deal_breaking_damage(source_unit, target_unit, element, data.BreakScale.wind)


listen(EventWeaknessBreak, _on_weakness_break, Priority.Event.weakness_break)
