from game import ActionFlag, Source, Unit, listen
from game.stats import *

from ..buff import Buff, TickType
from ..characters import Memosprite, MemospriteTracer
from ..events import EventAction
from .relic import Relic


class CRITDMGBoost(Buff):
    def __init__(self, source: Source | None, unit: Unit) -> None:
        super().__init__(source, "CRIT DMG Boost", unit, 2, TickType.start_end)
        self.stats = Stats(CRIT_DMG(0.2))

    def add(self):
        self.unit.stats += self.stats
        return super().add()

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()


class HeroOfTriumphantSong(Relic):
    def __init__(self, unit: Unit, stats: Stats, four_pc: bool) -> None:
        super().__init__("Hero of Triumphant Song", unit, stats)
        self.four_pc = four_pc
        self.spd = SPD()
        self.spd.get_increase = self.get_spd_boost
        self.stats.stats.extend((ATK(increase=0.12), self.spd))

    def add(self):
        self.listener = listen(EventAction, self.on_action)
        return super().add()

    def remove(self):
        self.listener.remove()
        return super().remove()

    def get_spd_boost(self):
        if not self.four_pc:
            return 0.0
        if self.unit.get_mod(MemospriteTracer) is None:
            return 0.0
        return 0.06

    def on_action(self, event: EventAction):
        if not self.four_pc:
            return
        if not isinstance(event.action.unit, Memosprite):
            return
        if event.action.unit.master is not self.unit:
            return
        if ActionFlag.attack not in event.action.flag:
            return
        CRITDMGBoost(self, event.action.unit).apply()
        CRITDMGBoost(self, self.unit).apply()
