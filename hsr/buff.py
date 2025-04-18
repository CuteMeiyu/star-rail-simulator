from dataclasses import dataclass
from enum import IntEnum, auto

from game.combat import EventTurn, EventTurnEnd, Mod, Unit
from game.event import Event, listen, trigger
from game.source import Source
from game.stats import *


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


class Buff(Mod):
    def __init__(self, source: Source | None, name: str, unit: Unit, duration: int, tick_type: TickType, dispelable=True, max_stack=0, priority=0) -> None:
        super().__init__(source, unit, priority)
        self._keep_ref = source
        self.name = name
        self.tick_type = tick_type
        self.started = False
        self.duration = duration
        self.max_stack = max_stack
        self.stacks = 0
        self.dispelable = dispelable

    def add(self):
        self.on_turn_start_listener = listen(EventTurn, self.on_turn_start)
        self.on_turn_end_listener = listen(EventTurnEnd, self.on_turn_end)
        super().add()
        trigger(EventBuffAdd(self))

    def remove(self):
        self._keep_ref = None
        self.on_turn_start_listener.remove()
        self.on_turn_end_listener.remove()
        super().remove()
        trigger(EventBuffRemove(self))

    def on_turn_start(self, event: EventTurn):
        if event.unit is not self.unit:
            return False
        self.started = True
        if self.tick_type == TickType.start:
            self.tick()
        return True

    def on_turn_end(self, event: EventTurnEnd):
        if event.unit is not self.unit:
            return False
        if self.tick_type == TickType.end:
            self.tick()
        elif self.started and self.tick_type == TickType.start_end:
            self.started = False
            self.tick()
        return True

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

    def stack(self, amount=1):
        self.stacks += amount
        self.stacks = min(self.stacks, self.max_stack)
