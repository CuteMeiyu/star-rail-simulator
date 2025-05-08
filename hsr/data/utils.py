from game.stats import *


def generate_lv10_data(start: float, step: float):
    return [i * step + start for i in range(10)]


def generate_lv15_data(start: float, step1: float, step2: float):
    seq1 = [i * step1 + start for i in range(6)]
    seq2 = [(i + 1) * step2 + seq1[-1] for i in range(4)]
    seq3 = [(i + 1) * step1 + seq2[-1] for i in range(5)]
    return seq1 + seq2 + seq3


_str_stat_map = {
    "hp": HP,
    "atk": ATK,
    "def": DEF,
    "spd": SPD,
    "taunt": Aggro,
    "crit_rate": CRIT_Rate,
    "crit_dmg": CRIT_DMG,
}


def generate_base_stats(data: dict[str, dict[str, float]], level: int, energy: float, path: PathFlag, element: ElementFlag):
    return Stats(
        *list(_str_stat_map[stat_type](data["base"] + data["step"] * (level - 1)) for stat_type, data in data.items()),
        Energy(energy),
        Level(level),
        Path(path),
        CombatType(element),
    )
