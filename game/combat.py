from bisect import insort_right
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Generic, TypeVar
from weakref import ref

from .chain import Chain, Node
from .event import Event, trigger
from .schedule import Runner, Schedule
from .source import Source
from .stats import *

_T = TypeVar("_T")


@dataclass
class EventTurn(Event):
    unit: "Unit"


@dataclass
class EventTurnEnd(Event):
    unit: "Unit"


@dataclass
class EventBattleStart(Event):
    battle: "Battle"


@dataclass
class EventNodeStart(Event):
    battle: "Battle"
    node: Node


@dataclass
class EventNodeEnd(Event):
    battle: "Battle"
    node: Node


@dataclass
class EventSkillPointChange(Event):
    source: Source | None
    team: "Team"
    amount: int


_T_Stat = TypeVar("_T_Stat", bound=Stat)


@dataclass
class EventStatusChange(Event, Generic[_T_Stat, _T]):
    source: Source | None
    unit: "Unit"
    stat_type: type[_T_Stat]
    previous: _T
    current: _T


@dataclass
class EventEnterBattle(Event):
    unit: "Unit"


class Mod(Source):
    def __init__(self, source: Source | None, unit: "Unit", priority=0) -> None:
        super().__init__(source)
        self._unit_ref = ref(unit)
        self.priority = priority

    @property
    def unit(self):
        unit = self._unit_ref()
        assert unit is not None
        return unit

    def add(self):
        insort_right(self.unit.mods, self, key=lambda mod: mod.priority)

    def remove(self):
        self.unit.mods.remove(self)

    def indicator(self) -> str:
        return ""


class SourcelessMod(Mod):
    def __init__(self, unit: "Unit", priority=0) -> None:
        super().__init__(None, unit, priority)


_T_Mod = TypeVar("_T_Mod", bound=Mod)


class StatusWrapper:
    def __init__(self, unit: "Unit", status: Status) -> None:
        self._unit_ref = ref(unit)
        self.status = status

    @property
    def unit(self):
        unit = self._unit_ref()
        assert unit is not None
        return unit

    def __getitem__(self, stat_type_or_tuple: type[Stat[_T]] | tuple[type[Stat[_T]], Source | None]) -> _T:
        if isinstance(stat_type_or_tuple, tuple):
            stat_type, _ = stat_type_or_tuple
        else:
            stat_type = stat_type_or_tuple
        return self.status[stat_type]

    def __setitem__(self, stat_type_or_tuple: type[Stat[_T]] | tuple[type[Stat[_T]], Source | None], value: _T):
        if isinstance(stat_type_or_tuple, tuple):
            stat_type, source = stat_type_or_tuple
        else:
            stat_type = stat_type_or_tuple
            source = None
        previous = self.status[stat_type]
        self.status[stat_type] = value
        trigger(EventStatusChange(source, self.unit, stat_type, previous, value))


class Unit(Runner, Source):
    def __init__(self, name: str, schedule_name: str, stats: Stats, team: "Team") -> None:
        super().__init__(schedule_name, 0.0)
        Source.__init__(self, None)
        self.name = name
        self.stats = stats
        self.status = StatusWrapper(self, Status({HP: stats[HP], Alive: True}))
        self.team = team
        self.mods: list[Mod] = []

    @property
    def battle(self):
        return self.team.battle

    @property
    def selectable(self):
        return self.status[Alive] and not self.stats[OffField]

    def get_speed(self):
        return self.stats[SPD]

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

    def add(self):
        self.team.add_unit(self)

    def remove(self):
        self.team.remove_unit(self)

    def select_adjacents(self):
        return self.team.select_adjacent_units(self)

    def select_allies(self):
        return self.team.select_all_units()

    def select_enemies(self):
        return [enemy for team in self.team.battle.teams if team is not self.team for enemy in team.units]


class Team:
    def __init__(self, battle: "Battle") -> None:
        self.units: list[Unit] = []
        self.battle = battle
        self.max_skill_point = 5
        self.skill_point = 3

    def add(self):
        self.battle.add_team(self)

    def remove(self):
        self.battle.remove_team(self)

    def lost(self):
        return all(not unit.status[Alive] for unit in self.units)

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

    def select_adjacent_units(self, unit: Unit):
        index = self.units.index(unit)
        targets: list[Unit] = []
        for indexer in range(index - 1, -1, -1), range(index + 1, len(self.units)):
            for i in indexer:
                if not self.units[i].selectable:
                    continue
                targets.append(self.units[i])
                break
        return targets

    def select_all_units(self):
        targets: list[Unit] = []
        for unit in self.units:
            if unit.selectable:
                targets.append(unit)
        return targets

    def gain_skill_point(self, source: Source | None, amount=1):
        sp = self.skill_point
        self.skill_point += amount
        self.skill_point = min(self.skill_point, self.max_skill_point)
        trigger(EventSkillPointChange(source, self, self.skill_point - sp))

    def cost_skill_point(self, source: Source | None, amount=1):
        sp = self.skill_point
        self.skill_point -= amount
        self.skill_point = max(self.skill_point, 0)
        trigger(EventSkillPointChange(source, self, self.skill_point - sp))


class BattlePhase(IntEnum):
    ready = auto()
    finish = auto()


class Battle:
    def __init__(self) -> None:
        self.teams: list[Team] = []
        self.schedule = Schedule()
        self.chain = Chain()
        self.current_unit: Unit | None = None
        self.started = False

    def start(self):
        self.started = True
        trigger(EventBattleStart(self))

    def is_over(self):
        return len([team for team in self.teams if not team.lost()]) <= 1

    def add_team(self, team: Team):
        self.teams.append(team)

    def remove_team(self, team: Team):
        self.teams.remove(team)

    def remove_dead_units(self):
        for team in self.teams:
            for unit in team.units.copy():
                if not unit.status[Alive] and not unit.stats[NoQuit]:
                    unit.remove()

    def run_nodes(self):
        for node in self.chain.flush():
            trigger(EventNodeStart(self, node))
            node.run()
            trigger(EventNodeEnd(self, node))

    def turn_in(self):
        while True:
            runner = self.schedule.turn_in()
            if isinstance(runner, Unit):
                self.current_unit = runner
                trigger(EventTurn(runner))
                self.run_nodes()
                return runner
            self.turn_out()

    def turn_out(self):
        self.remove_dead_units()
        runner = self.schedule.current_runner
        if runner not in self.schedule.runners:
            return
        self.schedule.turn_out()
        if isinstance(runner, Unit):
            trigger(EventTurnEnd(runner))
            self.run_nodes()

    def turn(self):
        while not self.is_over():
            yield BattlePhase.ready, self.turn_in()
            self.turn_out()
            assert self.current_unit is not None
            yield BattlePhase.finish, self.current_unit
