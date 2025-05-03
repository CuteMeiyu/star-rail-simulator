from hsr.characters.qingque import AutarkyBuff, Passive, Qingque

from ..console import ModSuffix, Suffix


class TileSuffix(Suffix):
    def string(self) -> str:
        passive = self.unit.get_mod(Passive)
        if passive is None:
            return ""
        return "".join(passive.tiles)


ModSuffix.table[AutarkyBuff] = "♠"


def init(qingque: Qingque):
    TileSuffix(qingque).add()
