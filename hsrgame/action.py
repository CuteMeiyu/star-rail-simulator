import random
from typing import Any, Sequence
from weakref import ref

from .chain import Node
from .combat import Mod, Unit
from .flexflag import FlexFlag
from .source import Source


class ActionFlag(FlexFlag):
    Attack: "ActionFlag"
    Single: "ActionFlag"
    Blast: "ActionFlag"
    AoE: "ActionFlag"
    Bounce: "ActionFlag"


class AttackFlag(FlexFlag):
    Basic: "AttackFlag"
    Skill: "AttackFlag"
    Ult: "AttackFlag"
    FUA: "AttackFlag"
    Counter: "AttackFlag"


AttackFlag.Counter |= AttackFlag.FUA


class Action(Node, Source):
    def __init__(self, name: str, unit: Unit, action_flag: ActionFlag, attack_flag: AttackFlag, priority=0) -> None:
        super().__init__(priority)
        Source.__init__(self, unit)
        self.name = name
        self.action_flag = action_flag
        self.attack_flag = attack_flag
        self.context: dict[str, Any] = {}
        self._main_target_ref = None
        self._targets_ref: list[ref[Unit]] = []

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
        return self.unit.status.alive

    def check(self):
        if not self.condition():
            return False
        if any(not asp.check_available(self) for asp in self.unit.get_mods(ActionSupressor)):
            return False
        return True

    def add_target(self, target: Unit):
        self._targets_ref.append(ref(target))

    def chain(self):
        self.unit.team.battle.chain.add(self)


class TargetAction(Action):
    def __init__(self, name: str, unit: Unit, target: Unit, action_flag: ActionFlag, attack_flag: AttackFlag, trans_target=False, priority=0) -> None:
        super().__init__(name, unit, action_flag, attack_flag, priority)
        self.trans_target = trans_target
        self.main_target = target
        self.add_target(target)

    def condition(self):
        if self.trans_target:
            return super().condition()
        else:
            return super().condition() and self.main_target is not None and self.main_target.selectable


class BounceAction(TargetAction):
    def bounce(self, hp_above_0=True, targets: list[Unit] | None = None):
        assert self.main_target is not None
        if targets is None:
            targets = self.main_target.get_ally()
        assert targets is not None
        available_targets: list[Unit] = []
        if hp_above_0:
            available_targets = [ally for ally in targets if ally.status.hp > 0]
        if len(available_targets) == 0:
            available_targets = targets
        target = random.choice(available_targets)
        if target not in self.targets:
            self.add_target(target)
        return target


class WeakAction(Action):
    def __init__(self, name: str, unit: Unit, priority=0) -> None:
        super().__init__(name, unit, ActionFlag(), AttackFlag(), priority)


class ActionProvider(Mod):
    def __init__(self, source: Source | None, unit: Unit, over_turn: bool) -> None:
        super().__init__(source, unit)
        self.over_turn = over_turn

    def get_available_actions(self) -> list[Action]:
        return []


class ActionSupressor(Mod):
    def check_available(self, action: Action):
        return True


class ActionController(Mod):
    def __init__(self, source: Source | None, unit: Unit, priority=0) -> None:
        super().__init__(source, unit)
        self.priority = priority

    def choose_action(self, actions: list[Action]) -> Action | None:
        return None
