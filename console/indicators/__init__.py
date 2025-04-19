from game.combat import Unit
from game.stats import *
from hsr.characters import Qingque

from ..console import NameIndicator, StatusSuffix, SuffixIndicator
from . import qingque


def init_indicators(unit: Unit):
    NameIndicator(unit).add()
    SuffixIndicator(unit).add()
    StatusSuffix(unit, HP).add()
    if unit.stats[Energy] > 0:
        StatusSuffix(unit, Energy).add()
    if unit.stats[Toughness] > 0:
        StatusSuffix(unit, Toughness).add()
    if isinstance(unit, Qingque):
        qingque.init(unit)
