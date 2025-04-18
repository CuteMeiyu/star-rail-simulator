from game import Action, ActionProvider, Unit, WeakAction
from game.stats import Energy

from .priority import Priority
from .turn import Turn


class UltExtraTurn(Turn):
    def __init__(self, unit: Unit, *ult_providers: ActionProvider, priority=0) -> None:
        super().__init__(unit, *ult_providers, priority=priority)
        self.name = "Extra Turn (Ult)"


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
