from game import ActionFlag, Source, Unit, UnitNode, listen
from game.events import EventActionEnd, EventTurn
from game.stats import *

from ..buff import DebuffFlag, TickType
from ..multipier import Multipier
from ..priority import Priority
from ..statusmanager import Damage, DamageFlag
from .control import Control
from .multipiers import DoTPercentMultipier, StackMultipier


class Entanglement(Control):
    def __init__(
        self,
        source: Source | None,
        name: str,
        source_unit: Unit,
        target_unit: Unit,
        duration: int,
        base_chance: float,
        fixed_chance: float,
        *damage_multipiers: Multipier,
        dispelable=True,
        max_stack=0,
        priority=0,
    ) -> None:
        super().__init__(source, name, source_unit, target_unit, duration, TickType.start, DebuffFlag.entanglement, base_chance, fixed_chance, dispelable, max_stack, priority)
        self.damage_multipiers = damage_multipiers

    def add(self):
        self.stack_listener = listen(EventActionEnd, self.on_action_end)
        return super().add()

    def remove(self):
        self.stack_listener.remove()
        return super().remove()

    def dot(self, percent=1.0):
        Damage(self, self.source_unit, self.unit, DamageFlag.additional, ElementFlag.quantum, *self.damage_multipiers, DoTPercentMultipier(percent), StackMultipier(max(self.stacks, 1))).deal()

    def on_action_end(self, event: EventActionEnd):
        if ActionFlag.attack not in event.action.flag:
            return
        if self.unit not in event.action.targets:
            return
        self.stack(1)


class EntanglementDamage(UnitNode):
    def run(self):
        for entanglement in self.unit.get_mods(Entanglement):
            entanglement.dot()


def _on_turn(event: EventTurn):
    if event.unit.get_mod(Entanglement):
        EntanglementDamage(event.unit).chain()


listen(EventTurn, _on_turn, Priority.Event.entanglement_dot)
