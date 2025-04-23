import random
from dataclasses import dataclass
from enum import IntEnum, auto

from game import Event, Mod, Source, Unit, listen, trigger
from game.events import EventTurn, EventTurnEnd
from game.stats import *

from .multipier import Calculator, Multipier
from .priority import Priority


class TickType(IntEnum):
    none = auto()
    start = auto()
    end = auto()
    start_end = auto()


@dataclass
class EventBuffAdd(Event):
    buff: "Buff"


@dataclass
class EventBuffExpired(Event):
    buff: "Buff"


@dataclass
class EventBuffRemove(Event):
    buff: "Buff"


@dataclass
class EventBuffDispel(Event):
    buff: "Buff"
    source: Source | None


@dataclass
class EventDebuffApply(Event):
    debuff: "Debuff"


@dataclass
class EventDebuffResistant(Event):
    debuff: "Debuff"


class Buff(Mod):
    def __init__(self, source: Source | None, name: str, unit: Unit, duration: int, tick_type: TickType, dispelable=True, max_stack=0, priority=0) -> None:
        super().__init__(source, unit, priority)
        self._keep_ref = source
        self.name = name
        self.tick_type = tick_type
        self.started = False
        self.duration = duration
        self.max_stack = max_stack
        self.stacks = min(max_stack, 1)
        self.dispelable = dispelable

    def add(self):
        if exist := self.get_stack_buff():
            exist.stack(self)
            return
        super().add()
        trigger(EventBuffAdd(self))

    def remove(self):
        self._keep_ref = None
        super().remove()
        trigger(EventBuffRemove(self))

    def tick(self):
        self.duration -= 1
        if self.duration <= 0:
            trigger(EventBuffExpired(self))
            self.remove()

    def dispel(self, source: Source | None):
        if not self.dispelable:
            return
        trigger(EventBuffDispel(self, source))
        self.remove()

    def set_stacks(self, stacks: int):
        self.stacks = max(0, min(stacks, self.max_stack))

    def stack(self, new_buff: "Buff"):
        self.set_stacks(self.stacks + new_buff.stacks)
        self.duration = max(self.duration, new_buff.duration)
        self.started = False

    def get_stack_buff(self):
        for exist in self.unit.get_mods(type(self)):
            if exist.get_source(Unit) is self.get_source(Unit):
                return exist
        return None


class Debuff(Buff, Calculator):
    def __init__(
        self,
        source: Source | None,
        name: str,
        source_unit: Unit,
        target_unit: Unit,
        duration: int,
        tick_type: TickType,
        debuff_flag: DebuffFlag,
        base_chance: float,
        fixed_chance: float,
        dispelable=True,
        max_stack=0,
        priority=0,
    ) -> None:
        super().__init__(source, name, target_unit, duration, tick_type, dispelable, max_stack, priority)
        self.debuff_flag = debuff_flag
        Calculator.__init__(self)
        self.source_unit = source_unit
        self.base_chance = base_chance
        self.fixed_chance = fixed_chance
        self.rng = random.random()
        self.source_stats = Stats()
        self.target_stats = Stats()
        self.source_stats += source_unit.stats
        self.target_stats += target_unit.stats
        self.add_multipiers(
            BaseHitRateMultipier(),
            EffectHitMultipier(),
            EffectRESMultipier(),
        )

    def calc(self):
        with self.source_stats.temp(flag=self.debuff_flag):
            with self.target_stats.temp(flag=self.debuff_flag):
                return super().calc()

    def is_hit(self):
        if self.rng < self.calc():
            return True
        if self.rng < self.fixed_chance:
            return True
        return False

    def apply(self):
        trigger(EventDebuffApply(self))
        if not self.is_hit():
            trigger(EventDebuffResistant(self))
            return
        self.add()


class BaseHitRateMultipier(Multipier[Debuff]):
    def get(self, calculator) -> float:
        return calculator.base_chance


class EffectHitMultipier(Multipier[Debuff]):
    def get(self, calculator) -> float:
        return 1.0 + calculator.source_stats[Effect_Hit_Rate]


class EffectRESMultipier(Multipier[Debuff]):
    def get(self, calculator) -> float:
        return 1.0 - calculator.target_stats.get(Effect_RES, debuff_flag=calculator.debuff_flag)


def _on_turn_start(event: EventTurn):
    for buff in event.unit.get_mods(Buff):
        buff.started = True
        if buff.tick_type == TickType.start:
            buff.tick()


def _on_turn_end(event: EventTurnEnd):
    for buff in event.unit.get_mods(Buff):
        if buff.tick_type == TickType.end:
            buff.tick()
        elif buff.started and buff.tick_type == TickType.start_end:
            buff.started = False
            buff.tick()


listen(EventTurn, _on_turn_start, Priority.Event.buff_tick)
listen(EventTurnEnd, _on_turn_end, Priority.Event.buff_tick)
