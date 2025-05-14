from game import Source, Unit, listen
from game.events import EventAction
from game.stats import *

from ..buff import Buff, TickType
from ..characters import Memosprite
from ..data import utils
from .utils import Lightcone


class FinalHit(Buff):
    def __init__(self, source: Source | None, unit: Unit) -> None:
        super().__init__(source, "Final Hit", unit, 3, TickType.start_end)

    def add(self):
        assert isinstance(self.source, VictoryInABlink)
        self.stats = Stats(DMG_Boost(utils.get_lightcone_data(self.source.id, self.source.superimposition)[1]))
        self.unit.stats += self.stats
        return super().add()

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()


class VictoryInABlink(Lightcone):
    def __init__(self, unit: Unit, ascension=6, level=80, superimposition=5) -> None:
        super().__init__(unit, "21050", ascension, level, superimposition)

    def add(self):
        crit_dmg = utils.get_lightcone_data(self.id, self.superimposition)[0]
        self.stats.stats.append(CRIT_DMG(crit_dmg))
        self.listener = listen(EventAction, self.on_action)
        return super().add()

    def remove(self):
        self.listener.remove()
        return super().remove()

    def on_action(self, event: EventAction):
        if not isinstance(event.action.unit, Memosprite):
            return
        if event.action.unit.master is not self.unit:
            return
        for ally in self.unit.select_allies():
            FinalHit(self, ally).apply()
