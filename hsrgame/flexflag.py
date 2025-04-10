from typing import Any, Self, overload


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
        for attr_name, anno_type_name in dict["__annotations__"].items():
            if anno_type_name != cls_name:
                continue
            setattr(cls, attr_name, cls.auto())


class FlexFlag(metaclass=MetaFlexFlag):
    _shift = 0

    def __init__(self, value=0) -> None:
        self.value = value

    def __eq__(self, other: object):
        assert isinstance(other, type(self))
        return self.value == other.value

    def __contains__(self, other: Self):
        return other.value & self.value == other.value

    def __str__(self):
        return str(self.value)

    @overload
    def __or__(self, other: Self) -> Self: ...  # type: ignore

    @overload
    def __or__(self, other: "FlexFlag") -> "MixFlag": ...

    def __or__(self, other: "Self | FlexFlag | MixFlag") -> "Self | MixFlag":
        if type(self) is type(other):
            assert isinstance(other, FlexFlag)
            return type(self)(self.value | other.value)
        return MixFlag(self, other)

    def __ior__(self, other: Self):
        self.value |= other.value
        return self

    def __invert__(self) -> Self:
        return type(self)(~self.value)

    @classmethod
    def auto(cls):
        flag = cls(1 << cls._shift)
        cls._shift += 1
        return flag


class MixFlag:
    def __init__(self, *flags: FlexFlag | Self) -> None:
        self.flag_dict: dict[type[FlexFlag], FlexFlag] = {}
        for flag in flags:
            self |= flag

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

    def __eq__(self, other: object):
        assert isinstance(other, MixFlag)
        for flag_type, flag in self.flag_dict.items():
            if flag_type not in self.flag_dict:
                return False
            if flag != self.flag_dict[flag_type]:
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
