from game import stats

from ..multipier import Multipier
from ..statusmanager import Damage


class BreakEffectMultipier(Multipier[Damage]):
    def get(self, calculator: Damage) -> float:
        return 1.0 + calculator.source_stats[stats.Break_Effect]


class ToughnessMultipier(Multipier[Damage]):
    def get(self, calculator: Damage) -> float:
        return (calculator.target_stats[stats.Toughness] + 20.0) * 0.025
