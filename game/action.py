import random
from dataclasses import dataclass
from typing import Any
from weakref import ref

from .chain import Node
from .combat import EventNodeEnd, EventNodeStart, Mod, Unit, UnitNode
from .event import Event, listen, trigger
from .flexflag import FlexFlag
from .source import Source
from .stats import *


@dataclass
class EventAction(Event):
    action: "Action"


@dataclass
class EventActionEnd(Event):
    action: "Action"


@dataclass
class EventAddTarget(Event):
    action: "Action"
    target: Unit


class ActionFlag(FlexFlag):
    attack: "ActionFlag"
    single: "ActionFlag"
    blast: "ActionFlag"
    aoe: "ActionFlag"
    bounce: "ActionFlag"
    basic: "ActionFlag"
    skill: "ActionFlag"
    ult: "ActionFlag"
    follow_up: "ActionFlag"
    counter: "ActionFlag"


ActionFlag.counter |= ActionFlag.follow_up


class Action(Node, Source):
    def __init__(self, name: str, unit: Unit, flag: ActionFlag, priority=0) -> None:
        super().__init__(priority)
        Source.__init__(self, unit)
        self.name = name
        self.flag = flag
        self.context: dict[str, Any] = {}
        self._main_target_ref = None
        self._targets_ref: list[ref[Unit]] = []
        self.conditions: list[ActionCondition] = [
            AliveCondition(),
            BrokenCondition(),
            SupressorCondition(),
        ]

    @property
    def unit(self):
        assert isinstance(self.source, Unit)
        return self.source

    @property
    def targets(self):
        targets: list[Unit] = []
        for target_ref in self._targets_ref:
            target = target_ref()
            if target is not None:
                targets.append(target)
        return targets

    @property
    def main_target(self):
        return None if self._main_target_ref is None else self._main_target_ref()

    @main_target.setter
    def main_target(self, main_target: Unit | None):
        self._main_target_ref = None if main_target is None else ref(main_target)

    @property
    def minor_targets(self):
        main_target = self.main_target
        for target in self.targets:
            if target != main_target:
                yield target

    def condition(self):
        return all(condition.check(self) for condition in self.conditions)

    def add_conditions(self, *conditions: "ActionCondition"):
        self.conditions.extend(conditions)

    def remove_condition(self, condition_type: type["ActionCondition"]):
        for condition in self.conditions.copy():
            if isinstance(condition, condition_type):
                self.conditions.remove(condition)

    def add_target(self, target: Unit):
        if target in self.targets:
            return
        self._targets_ref.append(ref(target))
        trigger(EventAddTarget(self, target))

    def chain(self, left_most=False):
        self.unit.team.battle.chain.add(self, left_most)


class BounceAction(Action):
    def bounce(self, ignore_limbo=True, targets: list[Unit] | None = None):
        if targets is None:
            targets = self.unit.select_enemies()
        available_targets: list[Unit] = []
        if ignore_limbo:
            available_targets = [ally for ally in targets if ally.status[HP] > 0]
        if len(available_targets) == 0:
            available_targets = targets
        target = random.choice(available_targets)
        self.add_target(target)
        return target


class WeakAction(Action):
    def __init__(self, name: str, unit: Unit, priority=0) -> None:
        super().__init__(name, unit, ActionFlag(), priority)


class ActionProvider(Mod):
    def __init__(self, source: Source | None, unit: Unit, over_turn: bool) -> None:
        super().__init__(source, unit)
        self.over_turn = over_turn

    def get_available_actions(self) -> list[Action]:
        return []


class ActionSupressor(Mod):
    def check_available(self, action: Action) -> bool:
        return True


class ActionCondition:
    def check(self, action: Action) -> bool: ...


class AliveCondition(ActionCondition):
    def check(self, action: Action) -> bool:
        return action.unit.status[Alive]


class BrokenCondition(ActionCondition):
    def check(self, action: Action):
        return not action.unit.status[Broken]


class SupressorCondition(ActionCondition):
    def check(self, action: Action) -> bool:
        return all(asp.check_available(action) for asp in action.unit.get_mods(ActionSupressor))


class MainTargetCondition(ActionCondition):
    def check(self, action: Action) -> bool:
        return action.main_target is not None and action.main_target.selectable


class Controller:
    def choose_action(self, actions: list[Action], allow_skip=False) -> Action | None: ...


class ActionSelector(Mod):
    def __init__(self, controller: Controller, unit: Unit, priority=0) -> None:
        super().__init__(None, unit, priority)
        self.controller = controller


def _on_node_start(event: EventNodeStart):
    if isinstance(event.node, Action) and not isinstance(event.node, WeakAction):
        trigger(EventAction(event.node))


def _on_node_end(event: EventNodeEnd):
    if isinstance(event.node, Action) and not isinstance(event.node, WeakAction):
        trigger(EventActionEnd(event.node))


listen(EventNodeStart, _on_node_start)
listen(EventNodeEnd, _on_node_end)
