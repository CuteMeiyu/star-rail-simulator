from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Any, TypeVar
from weakref import ref

from .chain import Chain, Node
from .event import Event, trigger
from .schedule import Runner, Schedule
from .source import Source
from .stats import *


class Mod(Source):
    def __init__(self, source: Source | None, unit: "Unit") -> None:
        super().__init__(source)
        self._unit_ref = ref(unit)

    @property
    def unit(self):
        unit = self._unit_ref()
        assert unit is not None
        return unit

    def add(self):
        self.unit.mods.append(self)

    def remove(self):
        self.unit.mods.remove(self)

    def indicator(self) -> str:
        return ""


_T_Mod = TypeVar("_T_Mod", bound=Mod)


@dataclass
class EventDead(Event):
    unit: "Unit"


class Death(Node):
    def __init__(self, unit: "Unit", priority=0) -> None:
        super().__init__(priority)
        self.unit = unit

    def run(self):
        self.unit.status.alive = False
        trigger(EventDead(self.unit))


@dataclass
class EventRevive(Event):
    unit: "Unit"
    source: Source | None


class ReviveNode(Node, Source):
    def __init__(self, source: Source | None, unit: "Unit", hp_percent: float, priority=0) -> None:
        super().__init__(priority)
        Source.__init__(self, source)
        self.unit = unit
        self.hp_percent = hp_percent

    def run(self):
        self.unit.status.alive = True
        self.unit.status.hp = self.unit.stats.get(HP) * self.hp_percent
        trigger(EventRevive(self.unit, self.source))


@dataclass
class Status:
    hp: float
    energy: float
    toughness: float
    alive: bool


class Unit(Runner, Source):
    def __init__(self, name: str, schedule_name: str, stats: Stats, team: "Team") -> None:
        super().__init__(schedule_name, 0.0)
        Source.__init__(self, None)
        self.name = name
        self.stats = stats
        self.status = Status(
            hp=self.stats.get(HP),
            energy=self.stats.get(Energy),
            toughness=self.stats.get(Toughness),
            alive=True,
        )
        self.team = team
        self.mods: list[Mod] = []
        team.add_unit(self)

    @property
    def selectable(self):
        return self.status.alive and not self.stats.get(OffField)

    def get_speed(self):
        return self.stats.get(SPD)

    def get_mod(self, mod_cls: type[_T_Mod]):
        for mod in self.mods:
            if isinstance(mod, mod_cls):
                return mod
        return None

    def get_mods(self, mod_cls: type[_T_Mod]):
        mods: list[_T_Mod] = []
        for mod in self.mods:
            if isinstance(mod, mod_cls):
                mods.append(mod)
        return mods

    def remove(self):
        self.team.remove_unit(self)

    def get_adjacent(self):
        return self.team.get_adjacent_units(self)

    def get_ally(self):
        return self.team.get_units()

    def regenerate_energy(self, amount: float, fixed: bool):
        if not fixed:
            amount *= 1.0 + self.stats.get(Energy_Regeneration_Rate)
        self.status.energy += amount
        self.status.energy = min(self.status.energy, self.stats.get(Energy))


@dataclass
class EventChangeSkillPoint(Event):
    source: Source | None
    team: "Team"
    amount: int


class Team:
    def __init__(self, battle: "Battle") -> None:
        self.units: list[Unit] = []
        self.battle = battle
        self.max_skill_point = 5
        self.skill_point = 3
        battle.add_team(self)

    def lost(self):
        return all(not unit.status.alive for unit in self.units)

    def add_unit(self, unit: Unit, index=-1):
        if index == -1:
            self.units.append(unit)
        elif index < 0:
            self.units.insert(index + 1, unit)
        else:
            self.units.insert(index, unit)
        self.battle.schedule.append(unit)

    def remove_unit(self, unit: Unit):
        for mod in unit.get_mods(Mod):
            mod.remove()
        self.units.remove(unit)
        self.battle.schedule.remove(unit)

    def get_adjacent_units(self, unit: Unit):
        index = self.units.index(unit)
        targets: list[Unit] = []
        for indexer in range(index - 1, -1, -1), range(index + 1, len(self.units)):
            for i in indexer:
                if not self.units[i].selectable:
                    continue
                targets.append(self.units[i])
                break
        return targets

    def get_units(self):
        targets: list[Unit] = []
        for unit in self.units:
            if unit.selectable:
                targets.append(unit)
        return targets

    def change_skill_point(self, source: Source | None, amount: int):
        trigger(EventChangeSkillPoint(source, self, amount))
        self.skill_point += amount
        self.skill_point = min(self.skill_point, self.max_skill_point)


@dataclass
class EventTurn(Event):
    unit: Unit


@dataclass
class EventTurnEnd(Event):
    unit: Unit


class BattlePhase(IntEnum):
    ready = auto()
    finish = auto()


class Battle:
    def __init__(self) -> None:
        self.teams: list[Team] = []
        self.schedule = Schedule()
        self.chain = Chain()
        self.current_unit: Unit | None = None

    def over(self):
        return len([team for team in self.teams if not team.lost()]) <= 1

    def add_team(self, team: Team):
        self.teams.append(team)

    def remove_team(self, team: Team):
        self.teams.remove(team)

    def turn_in(self):
        while True:
            runner = self.schedule.turn_in()
            if isinstance(runner, Unit):
                self.current_unit = runner
                trigger(EventTurn(runner))
                self.chain.flush()
                return runner
            self.turn_out()

    def turn_out(self):
        runner = self.schedule.current_runner
        self.schedule.turn_out()
        if isinstance(runner, Unit):
            trigger(EventTurnEnd(runner))
            self.chain.flush()

    def turn(self):
        while not self.over():
            yield BattlePhase.ready, self.turn_in()
            self.turn_out()
            yield BattlePhase.finish, self.current_unit
