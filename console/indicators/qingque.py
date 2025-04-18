from hsr.characters.qingque import Passive

from ..console import Suffix


class TileSuffix(Suffix):
    def string(self) -> str:
        passive = self.unit.get_mod(Passive)
        if passive is None:
            return ""
        return "".join(passive.tiles)
