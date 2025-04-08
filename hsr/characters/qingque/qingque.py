import random

from hsrgame.action import Action, ActionFlag, AttackFlag, WeakAction
from hsrgame.buff import Buff, TickType
from hsrgame.combat import EventTurn, Mod, Team, Unit
from hsrgame.damage import Damage, DamageFlag, ToughnessDamage
from hsrgame.event import listen
from hsrgame.source import Source
from hsrgame.stats import *

from ...character import Character, EventUnitReady, Turn
from ...data.characters import qingque as data
from ...priority import Priority


class Qingque(Character):
    def __init__(self, stats: Stats, team: Team, basic_level=6, skill_level=10, ult_level=10, talent_level=10, eidolon_level=0, trace_level=3) -> None:
        super().__init__("Qingque", "QQ", stats, team, basic_level, skill_level, ult_level, talent_level, eidolon_level, trace_level)
        Passive(self).add()


class HiddenHand(Buff):
    def __init__(self, source: Source | None, unit: Character) -> None:
        super().__init__(source, "Hidden Hand", unit, 1, TickType.end)
        self.stats = Stats(ATK(increase=data.talent_atk_boost[unit.talent_level - 1]))
        self.unit.stats += self.stats

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()


class HiddenHandAnimation(WeakAction):
    def __init__(self, unit: Unit) -> None:
        super().__init__("Hidden Hand", unit)


class Passive(Mod):
    def __init__(self, unit: Character) -> None:
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

    def is_win(self):
        return len(self.tiles) > 0 and self.tiles.count(self.tiles[0]) == 4

    def draw(self, n=1, pool: list[str] | None = None):
        assert isinstance(self.unit, Character)
        if pool is None:
            pool = self.pool
        if not self.is_win():
            self.performed = False
        for _ in range(n):
            self.tiles.append(random.choice(pool))
            self.tiles.sort(key=lambda x: (-self.tiles.count(x), self.tiles.index(x)))
            self.tiles = self.tiles[:4]
        if self.is_win():
            HiddenHand(self, self.unit).add()

    def pop(self):
        if len(self.tiles) == 0:
            return None
        return self.tiles.pop()

    def clear(self):
        self.tiles.clear()

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


class Basic(Action):
    def __init__(self, unit: Character, target: Unit) -> None:
        super().__init__("Flower Pick", unit, ActionFlag.attack | ActionFlag.single, AttackFlag.basic)
        self.main_target = target
        self.scale = data.basic_scale[unit.basic_level - 1]

    def run(self):
        assert self.main_target is not None
        self.unit.team.change_skill_point(self, 1)
        passive = self.unit.get_mod(Passive)
        if passive is not None:
            passive.pop()
        self.add_target(self.main_target)
        self.unit.regenerate_energy(20, False)
        Damage(self, self.unit, self.main_target, self.scale, DamageFlag.basic, CombatTypes.quantum).deal()
