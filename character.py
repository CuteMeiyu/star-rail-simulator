import random
from dataclasses import dataclass

from hsrgame.action import Action, ActionController, ActionProvider, ActionSupressor, WeakAction
from hsrgame.combat import Energy, Unit
from hsrgame.event import Event, trigger
from hsrgame.source import Source
from priority import Priority


@dataclass
class EventUnitReady(Event):
    unit: Unit
    turn: "Turn"


class Turn(WeakAction):
    def __init__(self, unit: Unit, specific_provider: ActionProvider | None = None, priority=Priority.Turn) -> None:
        super().__init__("Turn", unit, priority)
        self.specific_provider = specific_provider

    def run(self):
        trigger(EventUnitReady(self.unit, self))
        available_actions: list[Action] = []
        if self.specific_provider is not None:
            available_actions = self.specific_provider.get_available_actions()
        else:
            for provider in self.unit.get_mods(ActionProvider):
                actions = provider.get_available_actions()
                if provider.over_turn:
                    for action in actions:
                        action.context["over_turn"] = True
                available_actions += provider.get_available_actions()
        if len(available_actions) == 0:
            return
        for supressor in self.unit.get_mods(ActionSupressor):
            available_actions = [action for action in available_actions if supressor.check_available(action)]
        max_priority = 999
        controller = None
        for ac in self.unit.get_mods(ActionController):
            if ac.priority < max_priority:
                max_priority = ac.priority
                controller = ac
        if controller is not None:
            action = controller.choose_action(available_actions)
        else:
            action = random.choice(available_actions)
        if action is None:
            return
        action.chain()
        if "over_turn" in action.context:
            if action.priority < self.priority:
                self.chain()
            else:
                self.run()


class UltExtraTurn(Turn):
    def __init__(self, unit: Unit, ult_provider: ActionProvider, priority=0) -> None:
        super().__init__(unit, ult_provider, priority)


class UltActivate(WeakAction):
    def __init__(self, unit: Unit, ult_provider: ActionProvider, priority=Priority.UltActivate) -> None:
        super().__init__("Ult Activate", unit, priority)
        self.ult_provider = ult_provider

    def run(self):
        UltExtraTurn(self.unit, self.ult_provider).chain()


class UniversalUltActivator(ActionProvider):
    def __init__(self, unit: Unit, ult_provider: ActionProvider, min_energy_percent=1.0) -> None:
        super().__init__(unit, unit, True)
        self.ult_provider = ult_provider
        self.min_energy_percent = min_energy_percent

    def get_available_actions(self) -> list[Action]:
        if self.unit.status.energy >= self.unit.stats.get(Energy) * self.min_energy_percent:
            return [UltActivate(self.unit, self.ult_provider)]
        return []
