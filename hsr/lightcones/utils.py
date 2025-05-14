from game import Unit

from ..data import utils
from .lightcone import Lightcone as _Lightcone


class Lightcone(_Lightcone):
    def __init__(self, unit: Unit, id: str, ascension=6, level=80, superimposition=0) -> None:
        self.id = id
        self.ascension = ascension
        self.level = level
        self.superimposition = superimposition
        super().__init__(utils._lightcone_data[id]["name"], unit, utils.generate_lightcone_base_stats(id, ascension, level))
