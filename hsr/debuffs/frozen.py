from game import RunnerStatus, Source, Unit, UnitNode, listen
from game.events import EventTurn, EventTurnEnd
from game.stats import *

from ..buff import DebuffFlag, TickType
from ..multipier import Multipier
from ..priority import Priority
from ..statusmanager import Damage, DamageFlag
from .control import Control
from .multipiers import DoTPercentMultipier, StackMultipier


class Frozen(Control):
    def __init__(
        self,
        source: Source | None,
        name: str,
        source_unit: Unit,
        target_unit: Unit,
        duration: int,
        base_chance: float,
        fixed_chance: float,
        *multipiers: Multipier,
        dispelable=True,
        max_stack=0,
        priority=0,
    ) -> None:
        super().__init__(source, name, source_unit, target_unit, duration, TickType.start_end, DebuffFlag.frozen, base_chance, fixed_chance, dispelable, max_stack, priority)
        self.damage_multipiers = multipiers

    def dot(self, percent=1.0):
        Damage(
            self,
            self.source_unit,
            self.unit,
            self.flag | DamageFlag.additional | ElementFlag.ice,
            *self.damage_multipiers,
            DoTPercentMultipier(percent),
            StackMultipier(max(self.stacks, 1)),
        ).deal()


class FrozenDamage(UnitNode):
    def run(self):
        for frozen in self.unit.get_mods(Frozen):
            frozen.dot()


class Unfreeze(UnitNode):
    def run(self):
        self.unit.action_advance(5000, RunnerStatus.DELAYED)


def _on_turn(event: EventTurn):
    if event.unit.get_mod(Frozen):
        FrozenDamage(event.unit).chain()


def _on_turn_end(event: EventTurnEnd):
    if event.unit.get_mod(Frozen):
        Unfreeze(event.unit).chain()


listen(EventTurn, _on_turn, Priority.Event.frozen_dot)
listen(EventTurnEnd, _on_turn_end, Priority.Event.unfreeze)
