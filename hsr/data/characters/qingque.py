from game import stats

from .. import utils

id = "1201"

basic, skill, ult, talent = utils.get_character_abilities_data(id)
enhaused_basic = utils.get_ability_data(id, 8, "basic")


def generate_base_stats(ascension: int, level: int):
    return utils.generate_base_stats(id, ascension, level, 140, stats.PathFlag.erudition, stats.ElementFlag.quantum)


def generate_trace_stats(*trace_enabled: bool):
    return utils.generate_trace_stats(id, *trace_enabled)
