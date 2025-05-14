import math
from dataclasses import dataclass
from typing import Any

from game import Event, Mod, Source, Unit, UnitNode, listen, trigger
from game.events import EventStatusChange
from game.stats import *

from ..priority import Priority
from .status.hp import Damage


@dataclass
class EventDeath(Event):
    node: "Death"


class Death(UnitNode, Source):
    def __init__(self, source: Source | None, unit: Unit, priority=Priority.Node.death) -> None:
        super().__init__(unit, priority)
        Source.__init__(self, source)

    def get_killer(self):
        if (damage := self.get_source(Damage)) is not None:
            return damage.source_unit
        return self.get_source(Unit)

    def run(self):
        self.unit.status[Alive] = False
        trigger(EventDeath(self))


class DeathProtection(Mod):
    def protect(self, source: Source | None): ...


@dataclass
class EventWeaknessBreak(Event):
    source: Source | None
    unit: Unit


class BreakProtection(Mod):
    def protect(self): ...


def _on_status_change(event: EventStatusChange):
    if not isinstance(event.current, float | int) or isinstance(event.current, bool):
        return
    max_status = event.unit.stats[event.stat_type]
    if event.current > max_status:
        event.unit.status.status[event.stat_type] = max_status
        event.current = max_status
    elif event.current <= 0 or math.isclose(event.current, 0.0):
        event.unit.status.status[event.stat_type] = 0.0
        event.current = 0.0
        if event.previous <= 0:
            return
        if event.stat_type == HP:
            if not event.unit.status[Alive] or any(isinstance(node, Death) and node.unit is event.unit for node in event.unit.battle.chain.nodes):
                return
            if protection := event.unit.get_mod(DeathProtection):
                protection.protect(event.source)
            else:
                Death(event.source, event.unit).chain()
        elif event.stat_type == Toughness:
            if event.unit.status[Broken]:
                return
            if protection := event.unit.get_mod(BreakProtection):
                protection.protect()
            else:
                event.unit.status[Broken] = True
                event.unit.action_delay(2500)
                trigger(EventWeaknessBreak(event.source, event.unit))


listen(EventStatusChange, _on_status_change, Priority.Event.status_cap)
