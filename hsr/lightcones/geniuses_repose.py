from game import Source, Unit, listen
from game.stats import *

from ..buff import Buff, TickType
from ..data import utils
from ..events import EventDeath
from ..statusmanager import Damage
from .utils import Lightcone


class EachNowHasARoleToPlay(Buff):
    def __init__(self, source: Source | None, unit: Unit) -> None:
        super().__init__(source, "Each Now Has a Role to Play", unit, 3, TickType.start_end)

    def add(self):
        assert isinstance(self.source, GeniusesRepose)
        self.stats = Stats(CRIT_DMG(utils.get_lightcone_data(self.source.id, self.source.superimposition)[1]))
        self.unit.stats += self.stats
        return super().add()

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()


class GeniusesRepose(Lightcone):
    def __init__(self, unit: Unit, ascension=6, level=80, superimposition=5) -> None:
        super().__init__(unit, "21020", ascension, level, superimposition)

    def add(self):
        atk_boost = utils.get_lightcone_data(self.id, self.superimposition)[0]
        self.stats.stats.append(ATK(increase=atk_boost))
        self.listener = listen(EventDeath, self.on_death)
        return super().add()

    def remove(self):
        self.listener.remove()
        return super().remove()

    def on_death(self, event: EventDeath):
        if event.node.get_killer() is not self.unit:
            return
        EachNowHasARoleToPlay(self, self.unit).apply()
