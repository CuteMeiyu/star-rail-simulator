import math as _math
from contextlib import contextmanager as _contextmanager
from typing import Any as _Any
from typing import Generic as _Generic
from typing import Literal as _Literal
from typing import Self as _Self
from typing import TypeVar as _TypeVar

_T = _TypeVar("_T")


class Stat(_Generic[_T]):
    def __iadd__(self, other: _Self) -> _Self: ...
    def get_value(self) -> _T: ...


class _ComplexStat(Stat[float]):
    def __init__(self, base=0.0, flat=0.0, increase=0.0, decrease=0.0) -> None:
        self.base = base
        self.flat = flat
        self.increase = increase
        self.decrease = decrease

    def __iadd__(self, other: _Self) -> _Self:
        self.base += other.base
        self.flat += other.flat
        self.increase += other.increase
        self.decrease += other.decrease
        return self

    def get_value(self) -> float:
        return (self.base * (1 + self.increase) + self.flat) * (1 - self.decrease)


class ATK(_ComplexStat):
    pass


class DEF(_ComplexStat):
    pass


class HP(_ComplexStat):
    pass


class SPD(_ComplexStat):
    pass


class Aggro(_ComplexStat):
    pass


class Energy(_ComplexStat):
    pass


class Toughness(_ComplexStat):
    pass


class _SimpleStat(Stat[float]):
    def __init__(self, value=0.0) -> None:
        self.value = value

    def __iadd__(self, other: _Self) -> _Self:
        self.value += other.value
        return self

    def get_value(self) -> float:
        return self.value


class Break_Effect(_SimpleStat):
    pass


class CRIT_Rate(_SimpleStat):
    pass


class CRIT_DMG(_SimpleStat):
    pass


class DEF_Ignore(_SimpleStat):
    pass


class DMG_RES(_SimpleStat):
    pass


class RES_PEN(_SimpleStat):
    pass


class DMG_Boost(_SimpleStat):
    pass


class Effect_Hit_Rate(_SimpleStat):
    pass


class Energy_Regeneration_Rate(_SimpleStat):
    pass


class Outgoing_Healing_Boost(_SimpleStat):
    pass


class Vulnerability(_SimpleStat):
    pass


class Weaken(_SimpleStat):
    pass


DebuffName = _Literal["Bleed", "Burn", "Shock", "Wind Shear", "Frozen", "Entanglement", "Imprisonment", "Control", "Debuff"]


class Effect_RES(Stat[float]):
    def __init__(self, value=0.0, debuff_name: DebuffName = "Debuff") -> None:
        self.debuff_name = debuff_name
        self.multipiers: dict[str, float] = {debuff_name: 1 - value}

    def __iadd__(self, other: _Self) -> _Self:
        for debuff_name, value in other.multipiers.items():
            if debuff_name in self.multipiers:
                self.multipiers[debuff_name] += value - 1
            else:
                self.multipiers[debuff_name] = value
        return self

    def get_multipier(self, debuff_name: DebuffName = "Debuff"):
        return 1 - self.multipiers[debuff_name]

    def get_value(self) -> float:
        if any(value < 0 for value in self.multipiers.values()):
            return 1.0
        return 1 - _math.prod(self.multipiers.values())


class DMG_Mitigation(Stat[float]):
    def __init__(self, value=0.0) -> None:
        self.value = max(1 - value, 0)

    def __iadd__(self, other: _Self) -> _Self:
        self.value *= other.value
        return self

    def get_value(self) -> float:
        return 1 - self.value


class _GroupStat(Stat[tuple[str, ...]]):
    def __init__(self, *value: str):
        self.value = set(value)

    def __iadd__(self, other: _Self):
        self.value |= other.value
        return self

    def get_value(self):
        return tuple(self.value)


class Weakness(_GroupStat):
    pass


class Path(_GroupStat):
    pass


class CombatType(_GroupStat):
    pass


class _IntStat(Stat[int]):
    def __init__(self, value=0) -> None:
        self.value = value

    def __iadd__(self, other: _Self) -> _Self:
        self.value += other.value
        return self

    def get_value(self):
        return self.value


class Level(_IntStat):
    pass


class WeaknessDisable(_IntStat):
    pass


class OffField(_IntStat):
    pass


class OffTimeline(_IntStat):
    pass


_T_Stat = _TypeVar("_T_Stat", bound=Stat)


class Stats:
    def __init__(self, *stats: Stat[_Any], comment="") -> None:
        self.stats: list[Stat] = list(stats)
        self.children: list[Stats] = []
        self.comment = comment

    def get_stat(self, stat_type: type[_T_Stat], no_child=False, **kwargs: _Any) -> _T_Stat:
        stat = stat_type(**kwargs)
        stack: list[Stats] = [self]
        while len(stack) > 0:
            child = stack.pop()
            for s in child.stats:
                if isinstance(s, stat_type):
                    stat += s
            if not no_child:
                stack.extend(child.children)
        return stat

    def get(self, stat_type: type[Stat[_T]], no_child=False, **kwargs: _Any) -> _T:
        return self.get_stat(stat_type, no_child, **kwargs).get_value()

    @_contextmanager
    def temp(self, temp_stats: "Stats | None" = None):
        if temp_stats is not None:
            self += temp_stats
        try:
            yield
        finally:
            if temp_stats is not None:
                self -= temp_stats

    def __iadd__(self, other: _Self) -> _Self:
        self.children.append(other)
        return self

    def __isub__(self, other: _Self) -> _Self:
        self.children.remove(other)
        return self
