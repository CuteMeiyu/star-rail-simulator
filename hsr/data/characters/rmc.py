from game.stats import ElementFlag, PathFlag

from ..utils import generate_base_stats as _generate_base_stats

talent_hp = [
    [0.5, 400.0],
    [0.53, 424.0],
    [0.56, 448.0],
    [0.59, 472.0],
    [0.62, 496.0],
    [0.65, 520.0],
    [0.6875, 550.0],
    [0.725, 580.0],
    [0.7625, 610.0],
    [0.8, 640.0],
    [0.83, 664.0],
    [0.86, 688.0],
    [0.89, 712.0],
    [0.92, 736.0],
    [0.95, 760.0],
]
talent_energy_per = 10.0
talent_mem_energy = 0.01
basic_dmg_scale = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]
skill_heal = [0.3, 0.33, 0.36, 0.39, 0.42, 0.45, 0.4875, 0.525, 0.5625, 0.6, 0.63, 0.66, 0.69, 0.72, 0.75]
skill_energy = 0.1
ult_dmg_scale = [1.2, 1.32, 1.44, 1.56, 1.68, 1.8, 1.95, 2.1, 2.25, 2.4, 2.52, 2.64, 2.76, 2.88, 3.0]
ult_energy = 0.4
technique_action_delay = 0.5
technique_scale = 1.0

mem_talent_crit_dmg = [
    [0.06, 0.12],
    [0.072, 0.144],
    [0.084, 0.168],
    [0.096, 0.192],
    [0.108, 0.216],
    [0.12, 0.24],
    [0.132, 0.264],
    [0.144, 0.288],
    [0.156, 0.312],
    [0.168, 0.336],
    [0.06, 0.12],
    [0.072, 0.144],
    [0.084, 0.168],
    [0.096, 0.192],
    [0.108, 0.216],
    [0.12, 0.24],
    [0.132, 0.264],
    [0.144, 0.288],
    [0.156, 0.312],
    [0.168, 0.336],
]
mem_attack_dmg_scale = [
    [0.18, 0.45],
    [0.216, 0.54],
    [0.252, 0.63],
    [0.288, 0.72],
    [0.324, 0.81],
    [0.36, 0.9],
    [0.396, 0.99],
    [0.432, 1.08],
    [0.468, 1.17],
    [0.504, 1.26],
    [0.18, 0.45],
    [0.216, 0.54],
    [0.252, 0.63],
    [0.288, 0.72],
    [0.324, 0.81],
    [0.36, 0.9],
    [0.396, 0.99],
    [0.432, 1.08],
    [0.468, 1.17],
    [0.504, 1.26],
]
mem_support_scale = [0.18, 0.2, 0.22, 0.24, 0.26, 0.28, 0.3, 0.32, 0.34, 0.36, 0.18, 0.2, 0.22, 0.24, 0.26, 0.28, 0.3, 0.32, 0.34, 0.36]
mem_spawn_energy = 0.5
mem_despawn_action_advance = 2500.0

e1_dmg_crit = 0.1
e2_energy = 8
e3_skill_level = 2
e3_talent_level = 2
e3_memosprite_talent = 1
e4_mem_energy = 0.03
e4_true_dmg_scale = 0.06
e5_ult_level = 2
e5_basic_level = 1
e5_memosprite_skill = 1
e6_crit_rate = 1.0

trace_dmg = 0.373
trace_atk = 0.14
trace_hp = 0.14

t1_action_advance = 3000.0
t1_energy = 0.4
t2_energy = 0.05
t3_energy_exceed = 100.0
t3_energy_per = 10.0
t3_true_dmg_scale = 0.02
t3_true_dmg_scale_max = 0.2


ascesions = [
    {
        "hp": {"base": 142.56, "step": 7.128},
        "atk": {"base": 73.92, "step": 3.696},
        "def": {"base": 85.8, "step": 4.29},
        "spd": {"base": 103, "step": 0},
        "taunt": {"base": 100, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
    {
        "hp": {"base": 199.584, "step": 7.128},
        "atk": {"base": 103.488, "step": 3.696},
        "def": {"base": 120.12, "step": 4.29},
        "spd": {"base": 103, "step": 0},
        "taunt": {"base": 100, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
    {
        "hp": {"base": 256.608, "step": 7.128},
        "atk": {"base": 133.056, "step": 3.696},
        "def": {"base": 154.44, "step": 4.29},
        "spd": {"base": 103, "step": 0},
        "taunt": {"base": 100, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
    {
        "hp": {"base": 313.632, "step": 7.128},
        "atk": {"base": 162.624, "step": 3.696},
        "def": {"base": 188.76, "step": 4.29},
        "spd": {"base": 103, "step": 0},
        "taunt": {"base": 100, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
    {
        "hp": {"base": 370.656, "step": 7.128},
        "atk": {"base": 192.192, "step": 3.696},
        "def": {"base": 223.08, "step": 4.29},
        "spd": {"base": 103, "step": 0},
        "taunt": {"base": 100, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
    {
        "hp": {"base": 427.68, "step": 7.128},
        "atk": {"base": 221.76, "step": 3.696},
        "def": {"base": 257.4, "step": 4.29},
        "spd": {"base": 103, "step": 0},
        "taunt": {"base": 100, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
    {
        "hp": {"base": 484.704, "step": 7.128},
        "atk": {"base": 251.328, "step": 3.696},
        "def": {"base": 291.72, "step": 4.29},
        "spd": {"base": 103, "step": 0},
        "taunt": {"base": 100, "step": 0},
        "crit_rate": {"base": 0.05, "step": 0},
        "crit_dmg": {"base": 0.5, "step": 0},
    },
]


def generate_base_stats(level: int, ascesion_level: int):
    data = ascesions[ascesion_level]
    return _generate_base_stats(data, level, 160, PathFlag.remembrance, ElementFlag.ice)
