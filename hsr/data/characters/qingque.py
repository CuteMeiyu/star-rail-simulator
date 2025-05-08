from game.stats import *

from ..utils import generate_base_stats as _generate_base_stats
from ..utils import generate_lv10_data, generate_lv15_data

basic_scale = generate_lv10_data(0.5, 0.1)
enhaused_basic_main_scale = generate_lv10_data(1.2, 0.14)
enhaused_basic_minor_scale = generate_lv10_data(0.5, 0.1)
skill_dmg_boost = generate_lv15_data(0.14, 0.014, 0.0175)
ult_scale = generate_lv15_data(1.2, 0.08, 0.1)
talent_atk_boost = generate_lv15_data(0.36, 0.036, 0.045)

trace_atk_boost = 0.28
trace_dmg_boost = 0.144
trace_def_boost = 0.125

ascesions = [
    {
        "hp": {"base": 139.2, "step": 6.96},
        "atk": {"base": 88.8, "step": 4.44},
        "def": {"base": 60, "step": 3},
        "spd": {"base": 98, "step": 0},
        "taunt": {"base": 75, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
    {
        "hp": {"base": 194.88, "step": 6.96},
        "atk": {"base": 124.32, "step": 4.44},
        "def": {"base": 84, "step": 3},
        "spd": {"base": 98, "step": 0},
        "taunt": {"base": 75, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
    {
        "hp": {"base": 250.56, "step": 6.96},
        "atk": {"base": 159.84, "step": 4.44},
        "def": {"base": 108, "step": 3},
        "spd": {"base": 98, "step": 0},
        "taunt": {"base": 75, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
    {
        "hp": {"base": 306.24, "step": 6.96},
        "atk": {"base": 195.36, "step": 4.44},
        "def": {"base": 132, "step": 3},
        "spd": {"base": 98, "step": 0},
        "taunt": {"base": 75, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
    {
        "hp": {"base": 361.92, "step": 6.96},
        "atk": {"base": 230.88, "step": 4.44},
        "def": {"base": 156, "step": 3},
        "spd": {"base": 98, "step": 0},
        "taunt": {"base": 75, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
    {
        "hp": {"base": 417.6, "step": 6.96},
        "atk": {"base": 266.4, "step": 4.44},
        "def": {"base": 180, "step": 3},
        "spd": {"base": 98, "step": 0},
        "taunt": {"base": 75, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
    {
        "hp": {"base": 473.28, "step": 6.96},
        "atk": {"base": 301.92, "step": 4.44},
        "def": {"base": 204, "step": 3},
        "spd": {"base": 98, "step": 0},
        "taunt": {"base": 75, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
]


def generate_base_stats(level: int, ascesion_level: int):
    data = ascesions[ascesion_level]
    return _generate_base_stats(data, level, 140, PathFlag.erudition, ElementFlag.quantum)
