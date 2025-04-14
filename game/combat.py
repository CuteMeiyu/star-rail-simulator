from bisect import insort_right
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Any, TypeVar
from weakref import ref

from .chain import Chain, Node
from .event import Event, trigger
from .schedule import Runner, Schedule
from .source import Source
from .stats import *


@dataclass
class EventDead(Event):
    unit: "Unit"


@dataclass
class EventRevive(Event):
    unit: "Unit"
    source: Source | None


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
class EventHPChange(Event):
    source: Source | None
    unit: "Unit"
    amount: float


@dataclass
class EventEnergyChange(Event):
    source: Source | None
    unit: "Unit"
    amount: float


@dataclass
class EventToughnessChange(Event):
    source: Source | None
    unit: "Unit"
    amount: float


@dataclass
class EventSkillPointChange(Event):
    source: Source | None
    team: "Team"
    amount: int


@dataclass
class EventWeaknessBreak(Event):
    source: Source | None
    unit: "Unit"


@dataclass
class EventWeaknessRestore(Event):
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


_T_Mod = TypeVar("_T_Mod", bound=Mod)


class Death(Node, Source):
    def __init__(self, source: Source | None, unit: "Unit", priority=0) -> None:
        super().__init__(priority)
        Source.__init__(self, source)
        self.unit = unit

    def run(self):
        self.unit.status.alive = False
        trigger(EventDead(self.unit))


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


class WeaknessRestore(Node):
    def __init__(self, unit: "Unit", restore_percent=1.0, priority=0) -> None:
        super().__init__(priority)
        self.unit = unit
        self.restore_percent = restore_percent

    def run(self):
        self.unit.status.broken = False
        self.unit.status.toughness = self.unit.stats.get(Toughness) * self.restore_percent
        trigger(EventWeaknessRestore(self.unit))


class DeathProtection(Mod):
    def __init__(self, source: Source | None, unit: "Unit", count=1, priority=0) -> None:
        super().__init__(source, unit, priority)
        self.count = count

    def protect(self):
        self.count -= 1
        if self.count <= 0:
            self.remove()


class BreakProtection(Mod):
    def __init__(self, source: Source | None, unit: "Unit", count=1, priority=0) -> None:
        super().__init__(source, unit, priority)
        self.count = count

    def protect(self):
        self.count -= 1
        if self.count <= 0:
            self.remove()


@dataclass
class Status:
    hp: float
    energy: float
    toughness: float
    alive: bool
    broken: bool


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
            broken=False,
        )
        self.team = team
        self.mods: list[Mod] = []

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

    def add(self):
        self.team.add_unit(self)

    def remove(self):
        self.team.remove_unit(self)

    def get_adjacents(self):
        return self.team.get_adjacent_units(self)

    def get_allies(self):
        return self.team.get_units()

    def get_enemies(self):
        return [enemy for team in self.team.battle.teams if team is not self.team for enemy in team.units]

    def regenerate_energy(self, source: Source | None, amount: float, rated: bool):
        if rated:
            amount *= 1.0 + self.stats.get(Energy_Regeneration_Rate)
        self.change_energy(source, amount)

    def change_energy(self, source: Source | None, amount: float):
        energy = self.status.energy
        self.status.energy += amount
        self.status.energy = max(0.0, min(self.status.energy, self.stats.get(Energy)))
        trigger(EventEnergyChange(source, self, self.status.energy - energy))

    def change_hp(self, source: Source | None, amount: float):
        hp = self.status.hp
        self.status.hp += amount
        self.status.hp = min(max(self.status.hp, 0.0), self.stats.get(HP))
        trigger(EventHPChange(source, self, self.status.hp - hp))
        if self.status.hp <= 0.0:
            protection = self.get_mod(DeathProtection)
            if protection is not None:
                protection.protect()
            else:
                self.team.battle.chain.add(Death(source, self))

    def change_toughness(self, source: Source | None, amount: float):
        toughness = self.status.toughness
        self.status.toughness += amount
        self.status.toughness = min(max(self.status.toughness, 0.0), self.stats.get(Toughness))
        trigger(EventToughnessChange(source, self, self.status.toughness - toughness))
        if self.status.toughness <= 0.0:
            protection = self.get_mod(BreakProtection)
            if protection is not None:
                protection.protect()
            else:
                self.weakness_break(source)

    def weakness_break(self, source: Source | None):
        self.status.broken = True
        trigger(EventWeaknessBreak(source, self))


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
        trigger(EventSkillPointChange(source, self, amount))
        self.skill_point += amount
        self.skill_point = min(self.skill_point, self.max_skill_point)


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
        runner = self.schedule.current_runner
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
