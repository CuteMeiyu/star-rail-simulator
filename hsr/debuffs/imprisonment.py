from game.combat import Source, Unit
from game.stats import *

from ..buff import TickType
from .control import Control


class Imprisonment(Control):
    def __init__(
        self,
        source: Source | None,
        name: str,
        source_unit: Unit,
        target_unit: Unit,
        duration: int,
        base_chance: float,
        fixed_chance: float,
        speed_down=0.1,
        dispelable=True,
        max_stack=0,
        priority=0,
    ) -> None:
        super().__init__(source, name, source_unit, target_unit, duration, TickType.start, DebuffFlag.imprisonment, base_chance, fixed_chance, dispelable, max_stack, priority)
        self.speed_down = speed_down

    def add(self):
        self.stats = Stats(SPD(decrease=self.speed_down))
        self.unit.stats += self.stats
        super().add()

    def remove(self):
        self.unit.stats -= self.stats
        super().remove()
