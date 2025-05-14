from game import stats

from .. import utils

id = "8008"
basic, skill, ult, talent = utils.get_character_abilities_data(id)

mem_id = "18007"
mem_basic, mem_skill, mem_talent = utils.get_abilities_data(mem_id, [(1, "memosprite_skill"), (7, "memosprite_skill"), (3, "memosprite_talent")])


def generate_base_stats(ascension: int, level: int):
    return utils.generate_base_stats(id, ascension, level, 160, stats.PathFlag.remembrance, stats.ElementFlag.ice)


def generate_trace_stats(*trace_enabled: bool):
    return utils.generate_trace_stats(id, *trace_enabled)
