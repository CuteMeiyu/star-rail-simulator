import random

from game.action import Action, ActionFlag, ActionProvider
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


class A1(Action):
    def __init__(self, unit: Unit) -> None:
        super().__init__("A1", unit, ActionFlag.attack | ActionFlag.single)

    def run(self):
        enemies = self.unit.select_enemies()
        if len(enemies) == 0:
            return None
        self.main_target = random.choices(enemies, [enemy.stats.get(Aggro) for enemy in enemies], k=1)[0]
        self.add_target(self.main_target)
        deal_damage(self, self.unit, self.main_target, 1.0, 0.0, DamageFlag(), ElementFlag.ice)
        regenerate_energy(self, self.main_target, 5, True)


class AbilityProvider(ActionProvider):
    def __init__(self, unit: Unit) -> None:
        super().__init__(unit, unit, False)

    def get_available_actions(self) -> list[Action]:
        return [A1(self.unit)]
