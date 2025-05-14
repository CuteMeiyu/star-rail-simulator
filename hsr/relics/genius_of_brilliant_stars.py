from game import Unit, listen
from game.stats import *

from ..events import EventDamage
from .relic import Relic


class GeniusOfBrilliantStars(Relic):
    def __init__(self, unit: Unit, stats: Stats, four_pc: bool) -> None:
        super().__init__("Genius of Brilliant Stars", unit, stats)
        self.four_pc = four_pc
        self.stats.stats.append(DMG_Boost(0.1, ElementFlag.quantum))

    def add(self):
        self.listener = listen(EventDamage, self.on_damage)
        return super().add()

    def remove(self):
        self.listener.remove()
        return super().remove()

    def on_damage(self, event: EventDamage):
        if not self.four_pc:
            return
        if event.damage.source_unit is not self.unit:
            return
        if ElementFlag.quantum in event.damage.target_stats[Weakness]:
            decrease = 0.2
        else:
            decrease = 0.1
        event.damage.target_stats += Stats(DEF(decrease=decrease))
