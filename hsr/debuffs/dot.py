from game import Source, Unit, UnitNode, listen
from game.events import EventTurn
from game.stats import *

from ..buff import Debuff, DebuffFlag, TickType
from ..multipier import Multipier
from ..priority import Priority
from ..statusmanager import Damage, DamageFlag


class DoTPercentMultipier(Multipier[Damage]):
    def __init__(self, percent: float) -> None:
        super().__init__()
        self.percent = percent

    def get(self, calculator: Damage) -> float:
        return self.percent


class StackMultipier(Multipier[Damage]):
    def __init__(self, stacks: int) -> None:
        super().__init__()
        self.stacks = stacks

    def get(self, calculator: Damage) -> float:
        return self.stacks


class DoTDebuff(Debuff):
    def __init__(
        self,
        source: Source | None,
        name: str,
        source_unit: Unit,
        target_unit: Unit,
        duration: int,
        debuff_flag: DebuffFlag,
        base_chance: float,
        fixed_chance: float,
        damage_flag: DamageFlag,
        damage_type: ElementFlag,
        *multipiers: Multipier,
        dispelable=True,
        max_stack=0,
        priority=0,
    ) -> None:
        super().__init__(source, name, source_unit, target_unit, duration, TickType.start_end, debuff_flag, base_chance, fixed_chance, dispelable, max_stack, priority)
        self.damage_flag = damage_flag
        self.damage_type = damage_type
        self.damage_multipiers = multipiers

    def dot(self, percent=1.0):
        Damage(self, self.source_unit, self.unit, self.damage_flag, self.damage_type, *self.damage_multipiers, DoTPercentMultipier(percent), StackMultipier(max(self.stacks, 1))).deal()


class DoT(UnitNode):
    def run(self):
        for dot_debuff in self.unit.get_mods(DoTDebuff):
            dot_debuff.dot()


def _on_turn(event: EventTurn):
    if event.unit.get_mod(DoTDebuff):
        DoT(event.unit).chain()


listen(EventTurn, _on_turn, Priority.Event.dot)
