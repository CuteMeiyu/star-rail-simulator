import math
from typing import Generic, TypeVar
from weakref import ref


def clamp(value: float, lower_bound: float, upper_bound: float):
    return min(max(lower_bound, value), upper_bound)


_T_Calculator = TypeVar("_T_Calculator", bound="Calculator")


class Multipier(Generic[_T_Calculator]):
    def __init__(self, calculator: _T_Calculator):
        self._calculator_ref = ref(calculator)

    @property
    def calculator(self) -> _T_Calculator:
        calculator = self._calculator_ref()
        assert calculator is not None
        return calculator

    def get(self) -> float:
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

    def remove_multipier(self, multipier: Multipier):
        self.multipiers.remove(multipier)

    def update_multipier(self, multipier: Multipier):
        old_multipier = self.get_multipier(type(multipier))
        assert old_multipier is not None
        self.remove_multipier(old_multipier)
        self.add_multipier(multipier)

    def calc(self):
        return math.prod(multipier.get() for multipier in self.multipiers)

    def deal(self): ...
