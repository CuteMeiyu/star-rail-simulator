from hsr.characters.qingque import AutarkyBuff, Passive, Qingque

from ..console import ModSuffix, Suffix

ModSuffix.table[AutarkyBuff] = "♠"


class TileSuffix(Suffix):
    def string(self) -> str:
        passive = self.unit.get_mod(Passive)
        if passive is None:
            return ""
        return "".join(passive.tiles)


def init(qingque: Qingque):
    TileSuffix(qingque).add()
