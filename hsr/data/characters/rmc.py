from game import stats

from .. import utils

id = "8008"
(basic_scale,) = utils.get_ability_data(id, 1)
(skill_heal, skill_energy) = utils.get_ability_data(id, 2)
(ult_scale, ult_energy) = utils.get_ability_data(id, 3)
(talent_base_spd, talent_hp_percent, talent_energy_per, talent_hp_flat) = utils.get_ability_data(id, 4)
(technique_duration, technique_delay, technique_scale) = utils.get_ability_data(id, 7)

mem_id = "18007"
(mem_basic_bounce_scale, mem_basic_bounce_count, mem_basic_aoe_scale) = utils.get_ability_data(mem_id, 1)
(mem_talent_convert_cd, mem_talent_flat_cd) = utils.get_ability_data(mem_id, 3)
(mem_talent_energy,) = utils.get_ability_data(mem_id, 5)
(mem_talent_advance,) = utils.get_ability_data(mem_id, 6)
(mem_skill_scale, mem_skill_duration, mem_skill_advance) = utils.get_ability_data(mem_id, 7)

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

t1_action_advance = 3000.0
t1_energy = 0.4
t2_energy = 0.05
t3_energy_exceed = 100.0
t3_energy_per = 10.0
t3_true_dmg_scale = 0.02
t3_true_dmg_scale_max = 0.2


def generate_base_stats(ascension: int, level: int):
    return utils.generate_base_stats(id, ascension, level, 160, stats.PathFlag.remembrance, stats.ElementFlag.ice)


def generate_trace_stats(*trace_enabled: bool):
    return utils.generate_trace_stats(id, *trace_enabled)
