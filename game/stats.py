import math as _math
from contextlib import contextmanager as _contextmanager
from copy import deepcopy as _deepcopy
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


class PathFlag(_FlexFlag):
    hunt: "PathFlag"
    erudition: "PathFlag"
    harmony: "PathFlag"
    nihility: "PathFlag"
    remembrance: "PathFlag"
    destruction: "PathFlag"
    abundance: "PathFlag"
    preservation: "PathFlag"


class ConvertFlag(_FlexFlag):
    convert: "ConvertFlag"


class Stat(_Generic[_T]):
    def __init__(self, flag: _FlexFlag | _MixFlag | None = None, exclusive_flag: _FlexFlag | _MixFlag | None = None) -> None:
        if flag is None:
            self.flag = _MixFlag()
        else:
            self.flag = _MixFlag(flag)
        if exclusive_flag is None:
            self.exclusive_flag = _MixFlag()
        else:
            self.exclusive_flag = _MixFlag(exclusive_flag)

    def check_adapt(self, other: _Self):
        if other.flag not in self.flag:
            return False
        if len(self.exclusive_flag) > 0 and self.exclusive_flag in other.exclusive_flag:
            return False
        return True

    def __iadd__(self, other: _Self) -> _Self: ...
    def get_value(self) -> _T: ...


class _ComplexStat(Stat[float]):
    def __init__(self, base=0.0, flat=0.0, increase=0.0, decrease=0.0, flag: _FlexFlag | _MixFlag | None = None, exclusive_flag: _FlexFlag | _MixFlag | None = None) -> None:
        self.base = base
        self.flat = flat
        self.increase = increase
        self.decrease = decrease
        super().__init__(flag, exclusive_flag)

    def __iadd__(self, other: _Self) -> _Self:  # type: ignore
        self.base += other.get_base()
        self.flat += other.get_flat()
        self.increase += other.get_increase()
        self.decrease += other.get_decrease()
        return self

    def get_base(self):
        return self.base

    def get_flat(self):
        return self.flat

    def get_increase(self):
        return self.increase

    def get_decrease(self):
        return self.decrease

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
    def __init__(self, value=0.0, flag: _FlexFlag | _MixFlag | None = None, exclusive_flag: _FlexFlag | _MixFlag | None = None) -> None:
        self.value = value
        super().__init__(flag, exclusive_flag)

    def __iadd__(self, other: _Self) -> _Self:  # type: ignore
        self.value += other.get_value()
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
    def __init__(self, value=0.0, flag: _FlexFlag | _MixFlag | None = None, exclusive_flag: _FlexFlag | _MixFlag | None = None, debuff_flag: DebuffFlag | None = None) -> None:
        self.value = value
        self.multipiers: dict[int, float] = {}
        if debuff_flag is None:
            self.debuff_flag = DebuffFlag()
        else:
            self.debuff_flag = debuff_flag
        super().__init__(flag, exclusive_flag)

    def __iadd__(self, other: _Self) -> _Self:  # type: ignore
        if self.debuff_flag == other.debuff_flag:
            self.value += other.value
        elif other.debuff_flag in self.debuff_flag:
            if other.debuff_flag.value in self.multipiers:
                self.multipiers[other.debuff_flag.value] += other.value
            else:
                self.multipiers[other.debuff_flag.value] = other.value
        return self

    def get_value(self) -> float:
        return self.value * (1.0 - _math.prod(1.0 - min(value, 1.0) for value in self.multipiers.values()))


class DMG_Mitigation(Stat[float]):
    def __init__(self, value=0.0, flag: _FlexFlag | _MixFlag | None = None, exclusive_flag: _FlexFlag | _MixFlag | None = None) -> None:
        self.value = max(1 - value, 0)
        super().__init__(flag, exclusive_flag)

    def __iadd__(self, other: _Self) -> _Self:  # type: ignore
        self.value *= other.value
        return self

    def get_value(self) -> float:
        return 1 - self.value


_T_FlexFlag = _TypeVar("_T_FlexFlag", bound=_FlexFlag)


class _FlagStat(Stat[_T_FlexFlag], _Generic[_T_FlexFlag]):
    flag_type: type[_T_FlexFlag]

    def __init__(self, value: _T_FlexFlag | None = None, flag: _FlexFlag | _MixFlag | None = None, exclusive_flag: _FlexFlag | _MixFlag | None = None) -> None:
        super().__init__(flag, exclusive_flag)
        if value is not None:
            self.value = value
        else:
            self.value = self.flag_type()

    def __init_subclass__(cls, flag_type: type[_T_FlexFlag]) -> None:
        cls.flag_type = flag_type
        return super().__init_subclass__()

    def __iadd__(self, other: _Self) -> _Self:  # type: ignore
        self.value |= other.value
        return self

    def has_intersection(self, flag: _T_FlexFlag):
        return self.value.value & flag.value > 0

    def get_value(self) -> _T_FlexFlag:
        return self.value


class Weakness(_FlagStat[ElementFlag], flag_type=ElementFlag):
    pass


class Path(_FlagStat[PathFlag], flag_type=PathFlag):
    pass


class CombatType(_FlagStat[ElementFlag], flag_type=ElementFlag):
    pass


class _IntStat(Stat[int]):
    def __init__(self, value=0, flag: _FlexFlag | _MixFlag | None = None, exclusive_flag: _FlexFlag | _MixFlag | None = None) -> None:
        self.value = value
        super().__init__(flag, exclusive_flag)

    def __iadd__(self, other: _Self) -> _Self:  # type: ignore
        self.value += other.value
        return self

    def get_value(self):
        return self.value


class Level(_IntStat):
    pass


class WeaknessProtection(_IntStat):
    pass


class OffField(_IntStat):
    pass


class OffTimeline(_IntStat):
    pass


class NoQuit(_IntStat):
    pass


class BoolStat(Stat[bool]):
    default = False

    def __init__(self, flag: _FlexFlag | _MixFlag | None = None, exclusive_flag: _FlexFlag | _MixFlag | None = None) -> None:
        super().__init__(flag, exclusive_flag)
        self.value = self.default

    def __init_subclass__(cls, default: bool) -> None:
        cls.default = default
        return super().__init_subclass__()

    def __iadd__(self, other: _Self) -> _Self:  # type: ignore
        self.value = other.value
        return self

    def get_value(self) -> bool:
        return self.value


class Alive(BoolStat, default=True):
    pass


class Broken(BoolStat, default=False):
    pass


_T_Stat = _TypeVar("_T_Stat", bound=Stat)


class Stats:
    def __init__(self, *stats: Stat[_Any], comment="") -> None:
        self.stats: list[Stat[_Any]] = list(stats)
        self.children: list[Stats] = []
        self.locks: list[Stat[_Any]] = []
        self.comment = comment
        self._temp_flag: _FlexFlag | _MixFlag | None = None

    def get_stat(self, stat_type: type[_T_Stat], no_child=False, **kwargs: _Any) -> _T_Stat:
        for lock in self.locks:
            if type(lock) is stat_type:
                return lock
        if "flag" in kwargs and self._temp_flag is not None:
            kwargs["flag"] |= self._temp_flag
        else:
            kwargs["flag"] = self._temp_flag
        stat = stat_type(**kwargs)
        stack: list[Stats] = [self]
        while len(stack) > 0:
            child = stack.pop()
            for s in child.stats:
                if isinstance(s, stat_type) and stat.check_adapt(s):
                    stat += s
            if not no_child:
                stack.extend(child.children)
        return stat

    def get(self, stat_type: type[Stat[_T]], no_child=False, **kwargs: _Any) -> _T:
        return self.get_stat(stat_type, no_child, **kwargs).get_value()

    def __getitem__(self, stat_type: type[Stat[_T]]):
        return self.get(stat_type)

    def deepcopy(self):
        return _deepcopy(self)

    @_contextmanager
    def temp(self, stats: "Stats | None" = None, flag: _FlexFlag | _MixFlag | None = None):
        if stats is not None:
            self += stats
        self._temp_flag = flag
        try:
            yield
        finally:
            if stats is not None:
                self -= stats
            self._temp_flag = None

    def __iadd__(self, other: _Self) -> _Self:
        self.children.append(other)
        return self

    def __isub__(self, other: _Self) -> _Self:
        self.children.remove(other)
        return self


class Status:
    def __init__(self, dict: dict[type[Stat[_Any]], _Any]) -> None:
        self.dict = dict.copy()

    def __contains__(self, status_type: type[Stat[_T]]) -> bool:
        return status_type in self.dict

    def __getitem__(self, status_type: type[Stat[_T]]) -> _T:
        if status_type not in self.dict:
            return status_type().get_value()
        return self.dict[status_type]

    def __setitem__(self, status_type: type[Stat[_T]], value: _T):
        self.dict[status_type] = value
