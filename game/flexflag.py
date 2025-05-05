from typing import Any, Self, TypeVar, overload


class MetaFlexFlag(type):
    _skip = True

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)

    def __init__(cls, cls_name: str, bases: tuple[type, ...], dict: dict[str, Any]):
        super().__init__(cls_name, bases, dict)
        if MetaFlexFlag._skip:
            MetaFlexFlag._skip = False
            return
        assert issubclass(cls, FlexFlag), "MetaFlexFlag must be used on subclass of FlexFlag"
        cls._names = []
        for attr_name, anno_type_name in dict["__annotations__"].items():
            if anno_type_name != cls_name:
                continue
            setattr(cls, attr_name, cls.auto(attr_name))


class FlexFlag(metaclass=MetaFlexFlag):
    _shift = 0
    _names = []

    def __init__(self, value=0) -> None:
        self.value = value

    def __eq__(self, other: object):
        assert isinstance(other, type(self))
        return self.value == other.value

    def __contains__(self, other: Self):
        return other.value & self.value == other.value

    def __repr__(self):
        return f"{type(self).__name__}({', '.join(name for i, name in enumerate(self._names) if (1 << i) & self.value > 0)})"

    @overload
    def __or__(self, other: Self) -> Self: ...  # type: ignore

    @overload
    def __or__(self, other: "FlexFlag") -> "MixFlag": ...

    def __or__(self, other: "Self | FlexFlag | MixFlag") -> "Self | MixFlag":
        if type(self) is type(other):
            assert isinstance(other, type(self))
            return type(self)(self.value | other.value)
        return MixFlag(self, other)

    @overload
    def __and__(self, other: Self) -> Self: ...

    @overload
    def __and__(self, other: "MixFlag") -> "MixFlag": ...

    def __and__(self, other: "Self | MixFlag") -> Self | "MixFlag":
        if type(self) is type(other):
            assert isinstance(other, type(self))
            return type(self)(self.value & other.value)
        return other & self

    def __invert__(self) -> Self:
        return type(self)(~self.value)

    @classmethod
    def auto(cls, name: str):
        flag = cls(1 << cls._shift)
        cls._shift += 1
        cls._names.append(name)
        return flag


_T_FlexFlag = TypeVar("_T_FlexFlag", bound=FlexFlag)


class MixFlag:
    def __init__(self, *flags: FlexFlag | Self) -> None:
        self.flag_dict: dict[type[FlexFlag], FlexFlag] = {}
        for flag in flags:
            self |= flag

    def __len__(self):
        return len(self.flag_dict)

    def __repr__(self) -> str:
        return " | ".join(str(flag) for flag in self.flag_dict.values())

    def __getitem__(self, flag_type: type[_T_FlexFlag]) -> _T_FlexFlag:
        if flag_type not in self.flag_dict:
            return flag_type()
        return self.flag_dict[flag_type]

    def __or__(self, other: FlexFlag | Self):
        mix_flag = MixFlag(self)
        mix_flag |= other
        return mix_flag

    def __ior__(self, other: FlexFlag | Self):
        if isinstance(other, FlexFlag):
            if type(other) in self.flag_dict:
                self.flag_dict[type(other)] |= other
            else:
                self.flag_dict[type(other)] = other
        else:
            for flag_type, flag in other.flag_dict.items():
                if flag_type in self.flag_dict:
                    self.flag_dict[flag_type] |= flag
                else:
                    self.flag_dict[flag_type] = flag
        return self

    def __and__(self, other: FlexFlag | Self) -> "MixFlag":
        new_mix = MixFlag(self)
        new_mix &= other
        return new_mix

    def __iand__(self, other: FlexFlag | Self) -> Self:
        if isinstance(other, FlexFlag):
            to_remove = []
            for flag_type in self.flag_dict:
                if flag_type is type(other):
                    self.flag_dict[flag_type] &= other
                    if self.flag_dict[flag_type].value == 0:
                        to_remove.append(flag_type)
                else:
                    to_remove.append(flag_type)
        elif isinstance(other, MixFlag):
            to_remove = []
            for flag_type in self.flag_dict:
                if flag_type in other.flag_dict:
                    self.flag_dict[flag_type] &= other.flag_dict[flag_type]
                    if self.flag_dict[flag_type].value == 0:
                        to_remove.append(flag_type)
                else:
                    to_remove.append(flag_type)
        else:
            return NotImplemented
        for flag_type in to_remove:
            del self.flag_dict[flag_type]
        return self

    def __eq__(self, other: object):
        assert isinstance(other, MixFlag)
        for flag_type, flag in self.flag_dict.items():
            if flag_type not in other.flag_dict:
                return False
            if flag != other.flag_dict[flag_type]:
                return False
        return True

    def __contains__(self, other: FlexFlag | Self):
        if isinstance(other, FlexFlag):
            return type(other) in self.flag_dict and other in self.flag_dict[type(other)]
        for flag_type, flag in other.flag_dict.items():
            if flag_type not in self.flag_dict:
                return False
            if flag not in self.flag_dict[flag_type]:
                return False
        return True
