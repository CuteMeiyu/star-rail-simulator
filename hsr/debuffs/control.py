from game import ActionSupressor, Source, Unit
from game.action import Action
from game.stats import *

from ..buff import Debuff, TickType


class Control(Debuff, ActionSupressor):
    def __init__(
        self,
        source: Source | None,
        name: str,
        source_unit: Unit,
        target_unit: Unit,
        duration: int,
        tick_type: TickType,
        debuff_flag: DebuffFlag,
        base_chance: float,
        fixed_chance: float,
        dispelable=True,
        max_stack=0,
        priority=0,
    ) -> None:
        super().__init__(source, name, source_unit, target_unit, duration, tick_type, debuff_flag, base_chance, fixed_chance, dispelable, max_stack, priority)
        ActionSupressor.__init__(self, source, target_unit)

    def check_available(self, action: Action) -> bool:
        return False
