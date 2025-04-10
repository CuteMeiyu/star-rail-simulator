import math as _math
from contextlib import contextmanager as _contextmanager
from copy import deepcopy as _deepcopy
from enum import StrEnum as _StrEnum
from typing import Any as _Any
from typing import Generic as _Generic
from typing import Self as _Self
from typing import TypeVar as _TypeVar

from .flexflag import FlexFlag as _FlexFlag
from .flexflag import MixFlag as _MixFlag

_T = _TypeVar("_T")


class ElementFlag(_FlexFlag):
    physical: "ElementFlag"
    fire: "ElementFlag"
    lightning: "ElementFlag"
    wind: "ElementFlag"
    ice: "ElementFlag"
    quantum: "ElementFlag"
    imaginary: "ElementFlag"


class Stat(_Generic[_T]):
    def __init__(self, flag: _FlexFlag | _MixFlag | None = None) -> None:
        if flag is None:
            self.flag = _MixFlag()
        else:
            self.flag = _MixFlag(flag)

    def __iadd__(self, other: _Self) -> _Self: ...
    def get_value(self) -> _T: ...


class _ComplexStat(Stat[float]):
    def __init__(self, base=0.0, flat=0.0, increase=0.0, decrease=0.0, flag: _FlexFlag | _MixFlag | None = None) -> None:
        self.base = base
        self.flat = flat
        self.increase = increase
        self.decrease = decrease
        super().__init__(flag)

    def __iadd__(self, other: _Self) -> _Self:
        if other.flag not in self.flag:
            return self
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
    def __init__(self, value=0.0, flag: _FlexFlag | _MixFlag | None = None) -> None:
        self.value = value
        super().__init__(flag)

    def __iadd__(self, other: _Self) -> _Self:
        if other.flag not in self.flag:
            return self
        self.value += other.value
        return self

    def get_value(self) -> float:
        return self.value


class Break_Effect(_SimpleStat):
    pass


class Break_Efficiency(_SimpleStat):
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


class WeaknessIgnore(_SimpleStat):
    pass


class DebuffFlag(_FlexFlag):
    bleed: "DebuffFlag"
    burn: "DebuffFlag"
    shock: "DebuffFlag"
    wind_shear: "DebuffFlag"
    frozen: "DebuffFlag"
    entanglement: "DebuffFlag"
    imprisonment: "DebuffFlag"
    control: "DebuffFlag"
    dot: "DebuffFlag"


DebuffFlag.frozen |= DebuffFlag.control
DebuffFlag.entanglement |= DebuffFlag.control
DebuffFlag.imprisonment |= DebuffFlag.control
DebuffFlag.bleed |= DebuffFlag.dot
DebuffFlag.burn |= DebuffFlag.dot
DebuffFlag.shock |= DebuffFlag.dot
DebuffFlag.wind_shear |= DebuffFlag.dot


class Effect_RES(Stat[float]):
    def __init__(self, value=0.0, flag: DebuffFlag | None = None) -> None:
        self.value = value
        self.multipiers: dict[int, float] = {}
        if flag is None:
            self.buff_flag = DebuffFlag()
        else:
            self.buff_flag = flag
        super().__init__(None)

    def __iadd__(self, other: _Self) -> _Self:
        if self.buff_flag == other.buff_flag:
            self.value += other.value
        elif other.buff_flag in self.buff_flag:
            if other.buff_flag.value in self.multipiers:
                self.multipiers[other.buff_flag.value] += other.value
            else:
                self.multipiers[other.buff_flag.value] = other.value
        return self

    def get_value(self) -> float:
        return self.value * (1.0 - _math.prod(1.0 - min(value, 1.0) for value in self.multipiers.values()))


class DMG_Mitigation(Stat[float]):
    def __init__(self, value=0.0) -> None:
        self.value = max(1 - value, 0)

    def __iadd__(self, other: _Self) -> _Self:
        self.value *= other.value
        return self

    def get_value(self) -> float:
        return 1 - self.value


class _GroupStat(Stat[tuple[_T, ...]], _Generic[_T]):
    def __init__(self, *value: _T):
        self.value = set(value)

    def __iadd__(self, other: _Self):
        self.value |= other.value
        return self

    def get_value(self):
        return tuple(self.value)


class CombatType(_StrEnum):
    physical = "Physical"
    fire = "Fire"
    lightning = "Lightning"
    wind = "Wind"
    ice = "Ice"
    quantum = "Quantum"
    imaginary = "Imaginary"
    none = "None"


class Path(_StrEnum):
    destruction = "Destruction"
    preservation = "Preservation"
    hunt = "The Hunt"
    erudition = "Erudition"
    nihility = "Nihility"
    harmony = "Harmony"
    abundance = "Abundance"
    remembrance = "Remembrance"


class Weakness(_GroupStat[CombatType]):
    pass


class Paths(_GroupStat[Path]):
    pass


class CombatTypes(_GroupStat[CombatType]):
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


class WeaknessProtect(_IntStat):
    pass


class OffField(_IntStat):
    pass


class OffTimeline(_IntStat):
    pass


_T_Stat = _TypeVar("_T_Stat", bound=Stat)


class Stats:
    def __init__(self, *stats: Stat[_Any], comment="") -> None:
        self.stats: list[Stat[_Any]] = list(stats)
        self.children: list[Stats] = []
        self.comment = comment

    def get_stat(self, stat_type: type[_T_Stat], no_child=False, **kwargs: _Any) -> _T_Stat:
        stat = stat_type(**kwargs)
        stack: list[Stats] = [self]
        while len(stack) > 0:
            child = stack.pop()
            for s in child.stats:
                if type(s) is stat_type:
                    stat += s
            if not no_child:
                stack.extend(child.children)
        return stat

    def get(self, stat_type: type[Stat[_T]], no_child=False, **kwargs: _Any) -> _T:
        return self.get_stat(stat_type, no_child, **kwargs).get_value()

    def deepcopy(self):
        return _deepcopy(self)

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
