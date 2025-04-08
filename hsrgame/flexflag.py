from typing import Any, Self


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

    def __contains__(self, other: Self) -> bool:
        return other.value & self.value == other.value

    def __str__(self):
        return str(self.value)

    def __or__(self, other: Self) -> Self:
        return type(self)(self.value | other.value)

    def __ior__(self, other: Self) -> Self:
        self.value |= other.value
        return self

    @classmethod
    def auto(cls):
        flag = cls(1 << cls._shift)
        cls._shift += 1
        return flag
