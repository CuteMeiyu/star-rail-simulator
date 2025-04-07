from dataclasses import dataclass
from enum import IntEnum, auto

from .combat import EventTurn, EventTurnEnd, Mod, Unit
from .event import Event, listen, trigger
from .flexflag import FlexFlag
from .source import Source


class BuffFlag(FlexFlag):
    none: "BuffFlag"
    undispelable: "BuffFlag"
    indicator: "BuffFlag"
    debuff: "BuffFlag"
    control: "BuffFlag"
    dot: "BuffFlag"


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
    def __init__(self, source: Source | None, name: str, unit: Unit, duration: int, tick_type: TickType) -> None:
        super().__init__(source, unit)
        self.name = name
        self.tick_type = tick_type
        self.started = False
        self.duration = duration
        self.on_turn_start_listener = listen(EventTurn, self.on_turn_start)
        self.on_turn_end_listener = listen(EventTurnEnd, self.on_turn_end)
        trigger(EventBuffAdd(self))

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

    def remove(self):
        self.on_turn_start_listener.remove()
        self.on_turn_end_listener.remove()
        super().remove()
        trigger(EventBuffRemove(self))

    def dispel(self, source: Source | None):
        trigger(EventBuffDispel(self, source))
