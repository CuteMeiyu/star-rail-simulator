import random

from game import conditions
from game.action import Action, ActionFlag, ActionProvider, ActionSelector, Controller
from game.combat import Team, Unit
from game.stats import *

from ..statusmanager import DamageFlag, deal_damage, regenerate_energy
from ..units import Enemy


class Dummy(Enemy):
    def __init__(self, team: Team) -> None:
        super().__init__(
            "Dummy",
            "Dummy",
            Stats(
                ATK(1000),
                HP(10000),
                SPD(120),
                Toughness(60),
                Weakness(ElementFlag.quantum | ElementFlag.fire | ElementFlag.lightning),
            ),
            team,
            True,
        )
        AbilityProvider(self).add()
        ActionSelector(DummyController(), self).add()


class A1(Action):
    def __init__(self, unit: Unit, target: Unit) -> None:
        super().__init__("A1", unit, ActionFlag.attack | ActionFlag.single)
        self.main_target = target
        self.add_conditions(conditions.MainTargetCondition())

    def run(self):
        assert self.main_target is not None
        self.add_target(self.main_target)
        deal_damage(self, self.unit, self.main_target, 1.0, 0.0, DamageFlag(), ElementFlag.ice)
        regenerate_energy(self, self.main_target, 5, True)


class AbilityProvider(ActionProvider):
    def __init__(self, unit: Unit) -> None:
        super().__init__(unit, unit, False)

    def get_available_actions(self) -> list[Action]:
        return [A1(self.unit, enemy) for enemy in self.unit.select_enemies()]


class DummyController(Controller):
    def get_action_weight(self, action: Action):
        if action.main_target is None:
            return 0.0
        return action.main_target.stats[Aggro]

    def choose_action(self, actions: list[Action], allow_skip=False) -> Action | None:
        if len(actions) == 0:
            return None
        return random.choices(actions, weights=[self.get_action_weight(action) for action in actions], k=1)[0]
