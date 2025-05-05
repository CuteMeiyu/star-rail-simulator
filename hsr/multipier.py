import math
from typing import Generic, TypeVar

from game import FlexFlag, MixFlag, Source, Stats, Unit


def clamp(value: float, lower_bound: float, upper_bound: float):
    return min(max(lower_bound, value), upper_bound)


_T_Calculator = TypeVar("_T_Calculator", bound="Calculator")


class Multipier(Generic[_T_Calculator]):
    def get(self, calculator: _T_Calculator) -> float:
        return 1.0


_T_Multipier = TypeVar("_T_Multipier", bound=Multipier)


class Calculator:
    def __init__(self) -> None:
        self.multipiers: list[Multipier] = []

    def get_multipier(self, multipier_cls: type[_T_Multipier]) -> _T_Multipier | None:
        for multipier in self.multipiers:
            if isinstance(multipier, multipier_cls):
                return multipier
        return None

    def add_multipier(self, multipier: Multipier):
        assert self.get_multipier(type(multipier)) is None
        self.multipiers.append(multipier)

    def add_multipiers(self, *multipiers: Multipier):
        for multipier in multipiers:
            self.add_multipier(multipier)

    def remove_multipier(self, multipier_type: type[Multipier]):
        if multipier := self.get_multipier(multipier_type):
            self.multipiers.remove(multipier)

    def clear_multipier(self):
        self.multipiers.clear()

    def update_multipier(self, multipier: Multipier):
        old_multipier = self.get_multipier(type(multipier))
        assert old_multipier is not None
        self.multipiers.remove(old_multipier)
        self.add_multipier(multipier)

    def calc(self):
        return math.prod(multipier.get(self) for multipier in self.multipiers)

    def deal(self): ...


class SourceTargetCalculator(Calculator):
    def __init__(self, source_unit: Unit, target_unit: Unit, flag: None | FlexFlag | MixFlag, *multipiers: Multipier) -> None:
        super().__init__()
        self.source_unit = source_unit
        self.target_unit = target_unit
        self.source_stats = Stats()
        self.target_stats = Stats()
        self.source_stats += self.source_unit.stats
        self.target_stats += self.target_unit.stats
        self.flag = MixFlag() if flag is None else MixFlag(flag)
        self.add_multipiers(*multipiers)

    def calc(self):
        with self.source_stats.temp(flag=self.flag):
            with self.target_stats.temp(flag=self.flag):
                return super().calc()
