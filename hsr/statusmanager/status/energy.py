from dataclasses import dataclass

from game import Event, Source, Unit, trigger
from game.stats import *

from ..multipier import Calculator, Multipier


@dataclass
class EventEnergyRegenerate(Event):
    energy_regenerate: "EnergyRegenerate"


class EnergyRegenerate(Calculator, Source):
    def __init__(self, source: Source | None, unit: Unit, amount: float, apply_regeneration_rate: bool) -> None:
        super().__init__()
        Source.__init__(self, source)
        self.unit = unit
        self.amount = amount
        self.rated = apply_regeneration_rate
        self.add_multipiers(
            EnergyAmountMultipier(self),
            EnergyRegenerationRateMultipier(self),
        )

    def deal(self):
        trigger(EventEnergyRegenerate(self))
        amount = self.calc()
        self.unit.status[Energy, self] += amount


class EnergyAmountMultipier(Multipier[EnergyRegenerate]):
    def get(self) -> float:
        return self.calculator.amount


class EnergyRegenerationRateMultipier(Multipier[EnergyRegenerate]):
    def get(self) -> float:
        return 1.0 + self.calculator.unit.stats.get(Energy_Regeneration_Rate) if self.calculator.rated else 1.0
