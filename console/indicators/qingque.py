from hsr.characters.qingque import AutarkyBuff, Passive, Qingque

from ..console import Suffix


class TileSuffix(Suffix):
    def string(self) -> str:
        passive = self.unit.get_mod(Passive)
        if passive is None:
            return ""
        return "".join(passive.tiles)


class AutarkySuffix(Suffix):
    def string(self) -> str:
        return "Au" if self.unit.get_mod(AutarkyBuff) else ""


def init(qingque: Qingque):
    TileSuffix(qingque).add()
    AutarkySuffix(qingque).add()
