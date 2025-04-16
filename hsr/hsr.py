import math
import random
from dataclasses import dataclass

from game.action import Action, ActionProvider, Controller, ControllerGroup, WeakAction
from game.combat import Energy, Mod, Team, Unit
from game.event import Event, trigger
from game.stats import *

from .priority import Priority


@dataclass
class EventUnitReady(Event):
    unit: Unit
    turn: "Turn"


def get_available_actions(action_providers: list[ActionProvider], over_turn: bool):
    available_actions: list[Action] = []
    for provider in action_providers:
        if provider.over_turn != over_turn:
            continue
        actions = [action for action in provider.get_available_actions() if action.check()]
        available_actions += actions
    if over_turn:
        for action in available_actions:
            action.context["over_turn"] = True
    return available_actions


class Turn(WeakAction):
    def __init__(self, unit: Unit, *specific_providers: ActionProvider, priority=Priority.Node.turn) -> None:
        super().__init__("Turn", unit, priority)
        self.specific_providers = list(specific_providers)

    def run(self):
        trigger(EventUnitReady(self.unit, self))
        chain = self.unit.team.battle.chain
        if len(chain) > 0 and chain[0].priority < self.priority:
            self.chain(True)
            return
        while True:
            controller = self.unit.get_mod(Controller)
            group = None if controller is None else controller.group
            if len(self.specific_providers) > 0:
                available_actions = get_available_actions(self.specific_providers, False)
            else:
                available_actions = get_available_actions(self.unit.get_mods(ActionProvider), False)
            group_actions_dict: dict[ControllerGroup | None, list[Action]] = {group: available_actions}
            for ally in self.unit.team.units:
                ally_controller = ally.get_mod(Controller)
                ally_group = None if ally_controller is None else ally_controller.group
                ally_available_actions = get_available_actions(ally.get_mods(ActionProvider), True)
                if ally_group in group_actions_dict:
                    group_actions_dict[ally_group] += ally_available_actions
                else:
                    group_actions_dict[ally_group] = ally_available_actions
            action: Action | None = None
            for g, actions in group_actions_dict.items():
                if g is group or g is None or len(actions) == 0:
                    continue
                action = g.choose_action(actions, True)
                if action is not None:
                    break
            if action is None and len(group_actions_dict[group]) > 0:
                if group is None:
                    action = random.choice(group_actions_dict[group])
                else:
                    action = group.choose_action(group_actions_dict[group], False)
            if action is None:
                return
            if "over_turn" in action.context:
                action.chain(False)
                if action.priority < self.priority:
                    self.chain(True)
                else:
                    continue
            else:
                action.chain(True)
            break


class OverTurn(WeakAction):
    def __init__(self, unit: Unit) -> None:
        super().__init__("Action End", unit, Priority.Node.action_end)

    def run(self):
        group_actions_dict: dict[ControllerGroup | None, list[Action]] = {}
        for team in self.unit.team.battle.teams:
            for unit in team.units:
                controller = unit.get_mod(Controller)
                group = None if controller is None else controller.group
                actions = get_available_actions(unit.get_mods(ActionProvider), True)
                if group in group_actions_dict:
                    group_actions_dict[group] += actions
                else:
                    group_actions_dict[group] = actions
        for group, actions in group_actions_dict.items():
            if len(actions) == 0:
                continue
            if group is None:
                action = random.choice(actions)
            else:
                action = group.choose_action(actions, True)
            if action is not None:
                action.chain()
                return


class UltExtraTurn(Turn):
    def __init__(self, unit: Unit, ult_provider: ActionProvider, priority=0) -> None:
        super().__init__(unit, ult_provider, priority=priority)


class UltActivate(WeakAction):
    def __init__(self, unit: Unit, ult_provider: ActionProvider, priority=Priority.Node.ult_activate) -> None:
        super().__init__("Ult Activate", unit, priority)
        self.ult_provider = ult_provider

    def run(self):
        UltExtraTurn(self.unit, self.ult_provider).chain()


class UltActivator(ActionProvider):
    def __init__(self, unit: Unit, ult_provider: ActionProvider, min_energy_percent=1.0) -> None:
        super().__init__(unit, unit, True)
        self.ult_provider = ult_provider
        self.min_energy_percent = min_energy_percent

    def get_available_actions(self) -> list[Action]:
        if self.unit.status[Energy] < self.unit.stats.get(Energy) * self.min_energy_percent:
            return []
        for node in self.unit.team.battle.chain.nodes + [self.unit.team.battle.chain.current_node]:
            if isinstance(node, UltExtraTurn) and node.unit is self.unit:
                return []
        return [UltActivate(self.unit, self.ult_provider)]


class Character(Unit):
    def __init__(
        self,
        name: str,
        schedule_name: str,
        stats: Stats,
        team: Team,
        basic_level=6,
        skill_level=10,
        ult_level=10,
        talent_level=10,
        eidolon_level=0,
        trace_level=3,
    ) -> None:
        super().__init__(name, schedule_name, stats, team)
        self.basic_level = basic_level
        self.skill_level = skill_level
        self.ult_level = ult_level
        self.talent_level = talent_level
        self.trace_flag = 0
        self.set_trace_level(trace_level)
        self.eidolon_flag = 0
        self.set_eidolon_level(eidolon_level)

    def set_trace(self, t1: bool, t2: bool, t3: bool):
        self.trace_flag = (t1 << 2) | (t2 << 1) | (t3 << 0)

    def set_trace_level(self, trace_level: int):
        if trace_level > 3:
            trace_level = 3
        self.set_trace(trace_level >= 1, trace_level >= 2, trace_level >= 3)

    def check_trace(self, trace_level: int):
        return self.trace_flag & (0b1000 >> trace_level) > 0

    def enable_trace(self, trace_level: int):
        self.trace_flag |= 0b1000 >> trace_level

    def disable_trace(self, trace_level: int):
        self.trace_flag &= ~(0b1000 >> trace_level)

    def set_eidolon(self, e1: bool, e2: bool, e3: bool, e4: bool, e5: bool, e6: bool):
        self.eidolon_flag = (e1 << 5) | (e2 << 4) | (e3 << 3) | (e4 << 2) | (e5 << 1) | (e6 << 0)

    def set_eidolon_level(self, eidolon_level: int):
        if eidolon_level > 6:
            eidolon_level = 6
        self.set_eidolon(
            eidolon_level >= 1,
            eidolon_level >= 2,
            eidolon_level >= 3,
            eidolon_level >= 4,
            eidolon_level >= 5,
            eidolon_level >= 6,
        )

    def check_eidolon(self, eidolon_level: int):
        return self.eidolon_flag & (0b1000000 >> eidolon_level) > 0

    def enable_eidolon(self, eidolon_level: int):
        self.eidolon_flag |= 0b1000000 >> eidolon_level

    def disable_eidolon(self, eidolon_level: int):
        self.eidolon_flag &= ~(0b1000000 >> eidolon_level)


class Indicator(Mod):
    def string(self) -> str:
        return ""

    def modify_unit_string(self, unit_string: str) -> str:
        return unit_string


class StatusIndicator(Indicator):
    def __init__(self, unit: Unit, stat_type: type[Stat[float]], priority=0) -> None:
        super().__init__(None, unit, priority)
        self.stat_type = stat_type
        self.previous = unit.status[stat_type]

    def string(self):
        if not math.isclose(self.previous, self.unit.status[self.stat_type]):
            result = f"{int(self.previous)}{self.unit.status[self.stat_type]-self.previous:+.0f}"
        else:
            result = str(int(self.unit.status[self.stat_type]))
        self.previous = self.unit.status[self.stat_type]
        return result


class Enemy(Unit):
    def __init__(self, name: str, schedule_name: str, stats: Stats, team: Team) -> None:
        super().__init__(name, schedule_name, stats, team)
        self.status[Toughness] = self.stats[Toughness]
