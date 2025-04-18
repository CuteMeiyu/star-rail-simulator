import random
from dataclasses import dataclass

from game import Action, ActionProvider, ActionSelector, Controller, Event, Unit, WeakAction, trigger

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
            selector = self.unit.get_mod(ActionSelector)
            controller = None if selector is None else selector.controller
            if len(self.specific_providers) > 0:
                available_actions = get_available_actions(self.specific_providers, False)
            else:
                available_actions = get_available_actions(self.unit.get_mods(ActionProvider), False)
            controller_action_dict: dict[Controller | None, list[Action]] = {controller: available_actions}
            for ally in self.unit.team.units:
                ally_selector = ally.get_mod(ActionSelector)
                ally_controller = None if ally_selector is None else ally_selector.controller
                ally_available_actions = get_available_actions(ally.get_mods(ActionProvider), True)
                if ally_controller in controller_action_dict:
                    controller_action_dict[ally_controller] += ally_available_actions
                else:
                    controller_action_dict[ally_controller] = ally_available_actions
            action: Action | None = None
            for con, actions in controller_action_dict.items():
                if con is controller or con is None or len(actions) == 0:
                    continue
                action = con.choose_action(actions, True)
                if action is not None:
                    break
            if action is None and len(controller_action_dict[controller]) > 0:
                if controller is None:
                    action = random.choice(controller_action_dict[controller])
                else:
                    action = controller.choose_action(controller_action_dict[controller], False)
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
        controller_actions_dict: dict[Controller | None, list[Action]] = {}
        for team in self.unit.team.battle.teams:
            for unit in team.units:
                selector = unit.get_mod(ActionSelector)
                controller = None if selector is None else selector.controller
                actions = get_available_actions(unit.get_mods(ActionProvider), True)
                if controller in controller_actions_dict:
                    controller_actions_dict[controller] += actions
                else:
                    controller_actions_dict[controller] = actions
        for controller, actions in controller_actions_dict.items():
            if len(actions) == 0:
                continue
            if controller is None:
                action = random.choice(actions)
            else:
                action = controller.choose_action(actions, True)
            if action is not None:
                action.chain()
                return
