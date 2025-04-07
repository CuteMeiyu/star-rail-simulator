import random

import data.characters.qingque as data
from character import EventUnitReady, Turn
from hsrgame.action import Action, TargetAction, WeakAction
from hsrgame.buff import Buff, TickType
from hsrgame.combat import EventTurn, Mod, Team, Unit
from hsrgame.event import listen
from hsrgame.source import Source
from hsrgame.stats import *
from priority import Priority


class Qingque(Unit):
    def __init__(self, stats: Stats, team: Team) -> None:
        super().__init__("Qingque", "QQ", stats, team)
        self.basic_level = 6
        self.skill_level = 10
        self.ult_level = 10
        self.talent_level = 10
        self.eidolon_flag = 0b111111  # E1 -> E6
        Passive(self)


class HiddenHand(Buff):
    def __init__(self, source: Source | None, unit: Unit) -> None:
        super().__init__(source, "Hidden Hand", unit, 1, TickType.end)
        self.stats = Stats(ATK(increase=data.talent_atk_boost[self.qingque.talent_level - 1]))
        self.unit.stats += self.stats

    @property
    def qingque(self):
        assert isinstance(self.unit, Qingque)
        return self.unit

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()


class HiddenHandAnimation(WeakAction):
    def __init__(self, unit: Unit) -> None:
        super().__init__("Hidden Hand", unit, 0)


class Passive(Mod):
    def __init__(self, unit: Unit) -> None:
        super().__init__(unit, unit)
        self.tiles = []
        self.pool = ["Wan", "Tong", "Tiao"]
        self.on_turn_start_listener = listen(EventTurn, self.on_turn_start)
        self.on_unit_ready_listener = listen(EventUnitReady, self.on_unit_ready)
        self.performed = False

    def remove(self):
        self.on_turn_start_listener.remove()
        self.on_unit_ready_listener.remove()
        return super().remove()

    @property
    def qingque(self):
        assert isinstance(self.unit, Qingque)
        return self.unit

    def is_win(self):
        return len(self.tiles) > 0 and self.tiles.count(self.tiles[0]) == 4

    def draw(self, n=1, pool: list[str] | None = None):
        if self.qingque.eidolon_flag & 0b010000 > 0:
            self.qingque.gain_energy(1, True)
        if pool is None:
            pool = self.pool
        if not self.is_win():
            self.performed = False
        for _ in range(n):
            self.tiles.append(random.choice(pool))
            self.tiles.sort(key=lambda x: (-self.tiles.count(x), self.tiles.index(x)))
            self.tiles = self.tiles[:4]
        if self.is_win():
            HiddenHand(self, self.unit)

    def on_turn_start(self, event: EventTurn):
        if event.unit.team is not self.unit.team:
            return
        if self.is_win():
            return
        self.draw(1)

    def on_unit_ready(self, event: EventUnitReady):
        if event.unit is not self.unit:
            return
        if self.performed:
            return
        if not self.is_win():
            return
        self.performed = True
        HiddenHandAnimation(self.unit).chain()
