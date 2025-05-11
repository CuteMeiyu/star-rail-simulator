import json

from game import stats


def generate_lv10_data(start: float, step: float):
    return [i * step + start for i in range(10)]


def generate_lv15_data(start: float, step1: float, step2: float):
    seq1 = [i * step1 + start for i in range(6)]
    seq2 = [(i + 1) * step2 + seq1[-1] for i in range(4)]
    seq3 = [(i + 1) * step1 + seq2[-1] for i in range(5)]
    return seq1 + seq2 + seq3


with open("star_rail_res/character_promotions.json", encoding="utf-8") as f:
    _ascension_data = json.load(f)
with open("star_rail_res/character_ranks.json", encoding="utf-8") as f:
    _eidolon_data = json.load(f)
with open("star_rail_res/character_skill_trees.json", encoding="utf-8") as f:
    _trace_data = json.load(f)
with open("star_rail_res/character_skills.json", encoding="utf-8") as f:
    _ability_data = json.load(f)
with open("star_rail_res/characters.json", encoding="utf-8") as f:
    _character_data = json.load(f)

_str_base_stat_map = {
    "hp": stats.HP,
    "atk": stats.ATK,
    "def": stats.DEF,
    "spd": stats.SPD,
    "taunt": stats.Aggro,
    "crit_rate": stats.CRIT_Rate,
    "crit_dmg": stats.CRIT_DMG,
}


def generate_base_stats(character_id: str, ascension: int, level: int, energy: float, path: stats.PathFlag, element: stats.ElementFlag):
    data = _ascension_data[character_id]["values"]
    return stats.Stats(
        *[_str_base_stat_map[stat](base_step["base"] + base_step["step"] * (level - 1)) for stat, base_step in data[ascension].items()],
        stats.Level(level),
        stats.Energy(energy),
        stats.Path(path),
        stats.CombatType(element),
    )


_str_trace_stat_map = {
    "AttackAddedRatio": (stats.ATK, "increase", {}),
    "QuantumAddedRatio": (stats.DMG_Boost, "value", {"flag": stats.ElementFlag.quantum}),
    "DefenceAddedRatio": (stats.DEF, "increase", {}),
    "CriticalDamageBase": (stats.CRIT_DMG, "value", {}),
    "HPAddedRatio": (stats.HP, "increase", {}),
}


def generate_trace_stats(character_id: str, *trace_enabled: bool):
    data = [_trace_data[f"{character_id}2{i+1:02d}"]["levels"][0]["properties"][0] for i, enabled in enumerate(trace_enabled) if enabled]
    sum_stats_value = {}
    for i, trace in enumerate(data):
        if trace["type"] not in _str_trace_stat_map:
            raise ValueError(f"Unknown trace type: {trace['type']}")
        if trace["type"] not in sum_stats_value:
            sum_stats_value[trace["type"]] = 0.0
        sum_stats_value[trace["type"]] += trace["value"]
    stat_list = []
    for key, value in sum_stats_value.items():
        stat_type, value_type, kwargs = _str_trace_stat_map[key]
        stat_list.append(stat_type(**{value_type: value, **kwargs}))
    return stats.Stats(*stat_list)


def get_ability_data(character_id: str, ability: int):
    params = _ability_data[f"{character_id}{ability:02d}"]["params"]
    return tuple(zip(*params))


def get_trace_data(character_id: str, trace: int):
    params = _trace_data[f"{character_id}1{trace:02d}"]["params"]
    return tuple(zip(*params))
