from game import stats

from .. import utils

id = "1201"
(basic_scale,) = utils.get_ability_data(id, 1)
(skill_duration, skill_dmg_boost, skill_max_stack) = utils.get_ability_data(id, 2)
(ult_scale,) = utils.get_ability_data(id, 3)
(talent_atk_boost,) = utils.get_ability_data(id, 4)
(technique_draw_tiles,) = utils.get_ability_data(id, 7)
(enhaused_basic_main_scale, enhaused_basic_minor_scale) = utils.get_ability_data(id, 8)
t1_skill_point = 1
(t2_dmg_boost,) = utils.get_trace_data(id, 2)
(t3_spd_boost,) = utils.get_trace_data(id, 3)
e1_dmg_boost = 0.1
e2_energy = 1


def generate_basic_stats(ascension: int, level: int):
    return utils.generate_base_stats(id, ascension, level, 140, stats.PathFlag.erudition, stats.ElementFlag.quantum)


def generate_trace_stats(*trace_enabled: bool):
    return utils.generate_trace_stats(id, *trace_enabled)
