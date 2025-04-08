import random
from dataclasses import dataclass

from hsrgame.action import Action, ActionController, ActionProvider, ActionSupressor, WeakAction
from hsrgame.combat import Energy, Team, Unit
from hsrgame.event import Event, trigger
from hsrgame.stats import Stats

from .priority import Priority


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
        self.trace_flag = (t1 << 3) & (t2 << 2) & (t3 << 1)

    def set_trace_level(self, trace_level: int):
        if trace_level > 3:
            trace_level = 3
        self.set_trace(trace_level <= 1, trace_level <= 2, trace_level <= 3)

    def check_trace(self, trace_level: int):
        return self.trace_flag & (0b1000 >> trace_level) > 0

    def enable_trace(self, trace_level: int):
        self.trace_flag |= 0b1000 >> trace_level

    def disable_trace(self, trace_level: int):
        self.trace_flag &= ~(0b1000 >> trace_level)

    def set_eidolon(self, e1: bool, e2: bool, e3: bool, e4: bool, e5: bool, e6: bool):
        self.eidolon_flag = (e1 << 6) & (e2 << 5) & (e3 << 4) & (e4 << 3) & (e5 << 2) & (e6 << 1)

    def set_eidolon_level(self, eidolon_level: int):
        if eidolon_level > 6:
            eidolon_level = 6
        self.set_eidolon(
            eidolon_level <= 1,
            eidolon_level <= 2,
            eidolon_level <= 3,
            eidolon_level <= 4,
            eidolon_level <= 5,
            eidolon_level <= 6,
        )

    def check_eidolon(self, eidolon_level: int):
        return self.eidolon_flag & (0b1000000 >> eidolon_level) > 0

    def enable_eidolon(self, eidolon_level: int):
        self.eidolon_flag |= 0b1000000 >> eidolon_level

    def disable_eidolon(self, eidolon_level: int):
        self.eidolon_flag &= ~(0b1000000 >> eidolon_level)
