from typing import Any, Self


class MetaFlexFlag(type):
    skip = True

    def __init__(cls, cls_name: str, bases: tuple[type, ...], dict: dict[str, Any]):
        super().__init__(cls_name, bases, dict)
        if MetaFlexFlag.skip:
            MetaFlexFlag.skip = False
            return
        assert issubclass(cls, FlexFlag), "FlexFlagMeta must be used on subclass of FlexFlag"
        for attr_name, anno_type_name in dict["__annotations__"].items():
            if anno_type_name != cls_name:
                continue
            setattr(cls, attr_name, cls.auto())


class FlexFlag(metaclass=MetaFlexFlag):
    shift = 0

    def __init__(self, value=0) -> None:
        self.value = value

    def __contains__(self, other: Self) -> bool:
        return other.value & self.value == other.value

    @classmethod
    def auto(cls):
        flag = cls(1 << cls.shift)
        cls.shift += 1
        return flag

    def __str__(self):
        return str(self.value)

    def __or__(self, other: Self) -> Self:
        return type(self)(self.value | other.value)
