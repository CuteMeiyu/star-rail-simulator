import random

from game.action import Action, ActionFlag, ActionProvider, ControllerGroup
from game.combat import Team, Unit
from game.multipier import Damage, DamageFlag
from game.source import Source
from game.stats import *

from ..hsr import Enemy, StatusIndicator


class Dummy(Enemy):
    def __init__(self, team: Team) -> None:
        super().__init__(
            "Dummy",
            "Dummy",
            Stats(
                ATK(1000),
                HP(10000),
                SPD(158),
                Toughness(120),
                Weakness(CombatType.quantum, CombatType.fire, CombatType.lightning),
            ),
            team,
        )
        StatusIndicator(self, HP).add()
        StatusIndicator(self, Toughness).add()
        AbilityProvider(self).add()


class A1(Action):
    def __init__(self, unit: Unit) -> None:
        super().__init__("Simple Attack", unit, ActionFlag.attack | ActionFlag.single)

    def run(self):
        enemies = self.unit.select_enemies()
        if len(enemies) == 0:
            return None
        self.main_target = random.choices(enemies, [enemy.stats.get(Aggro) for enemy in enemies], k=1)[0]
        self.add_target(self.main_target)
        Damage(self, self.unit, self.main_target, 1.0, 0.0, DamageFlag(), CombatType.ice).deal()
        self.main_target.status[Energy, self] += 10.0 * (1.0 + self.main_target.stats[Energy_Regeneration_Rate])


class AbilityProvider(ActionProvider):
    def __init__(self, unit: Unit) -> None:
        super().__init__(unit, unit, False)

    def get_available_actions(self) -> list[Action]:
        return [A1(self.unit)]
