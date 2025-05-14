import json
from typing import Any, Literal

from game import Unit, stats

from ..characters import Character, Memosprite, RemembranceCharacter


def generate_lv10_data(start: float, step: float):
    return [i * step + start for i in range(10)]


def generate_lv15_data(start: float, step1: float, step2: float):
    seq1 = [i * step1 + start for i in range(6)]
    seq2 = [(i + 1) * step2 + seq1[-1] for i in range(4)]
    seq3 = [(i + 1) * step1 + seq2[-1] for i in range(5)]
    return seq1 + seq2 + seq3


with open("hsr/data/assets/character_promotions.json", encoding="utf-8") as f:
    _ascension_data = json.load(f)
with open("hsr/data/assets/character_ranks.json", encoding="utf-8") as f:
    _eidolon_data = json.load(f)
with open("hsr/data/assets/character_skill_trees.json", encoding="utf-8") as f:
    _trace_data = json.load(f)
with open("hsr/data/assets/character_skills.json", encoding="utf-8") as f:
    _ability_data = json.load(f)
with open("hsr/data/assets/characters.json", encoding="utf-8") as f:
    _character_data = json.load(f)
with open("hsr/data/assets/light_cone_promotions.json", encoding="utf-8") as f:
    _lightcone_ascension_data = json.load(f)
with open("hsr/data/assets/light_cone_ranks.json", encoding="utf-8") as f:
    _lightcone_superimposition_data = json.load(f)
with open("hsr/data/assets/light_cones.json", encoding="utf-8") as f:
    _lightcone_data = json.load(f)

_str_base_stat_map = {
    "hp": stats.HP,
    "atk": stats.ATK,
    "def": stats.DEF,
    "spd": stats.SPD,
    "taunt": stats.Aggro,
    "crit_rate": stats.CRIT_Rate,
    "crit_dmg": stats.CRIT_DMG,
}


def generate_character_base_stats(character_id: str, ascension: int, level: int, energy: float, path: stats.PathFlag, element: stats.ElementFlag):
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


AbilityType = Literal["basic", "skill", "ult", "talent", "memosprite_skill", "memosprite_talent", "technique"]


class AbilityData:
    def __init__(self, data: tuple, ability_type: AbilityType) -> None:
        self.data = data
        self.ability_type = ability_type

    def __call__(self, unit: Unit) -> Any:
        match self.ability_type:
            case "basic":
                assert isinstance(unit, Character)
                return self.data[unit.get_basic_level() - 1]
            case "skill":
                assert isinstance(unit, Character)
                return self.data[unit.get_skill_level() - 1]
            case "ult":
                assert isinstance(unit, Character)
                return self.data[unit.get_ult_level() - 1]
            case "talent":
                assert isinstance(unit, Character)
                return self.data[unit.get_talent_level() - 1]
            case "memosprite_skill":
                if isinstance(unit, Memosprite):
                    return self.data[unit.master.get_memosprite_skill_level() - 1]
                assert isinstance(unit, RemembranceCharacter)
                return self.data[unit.get_memosprite_skill_level() - 1]
            case "memosprite_talent":
                if isinstance(unit, Memosprite):
                    return self.data[unit.master.get_memosprite_talent_level() - 1]
                assert isinstance(unit, RemembranceCharacter)
                return self.data[unit.get_memosprite_talent_level() - 1]
            case "technique":
                return self.data[0]
        raise ValueError(f"unknwon ability_type: {self.ability_type}")


def get_ability_data(character_id: str, ability: int, level_type: AbilityType):
    return AbilityData(_ability_data[f"{character_id}{ability:02d}"]["params"], level_type)


def get_abilities_data(character_id: str, ability_type_tuple: list[tuple[int, AbilityType]]):
    return tuple(get_ability_data(character_id, aid, typ) for aid, typ in ability_type_tuple)


def get_character_abilities_data(id: str):
    return get_abilities_data(id, [(1, "basic"), (2, "skill"), (3, "ult"), (4, "talent")])


def get_trace_data(character_id: str, trace: int):
    return tuple(_trace_data[f"{character_id}1{trace:02d}"]["params"][0])


def generate_lightcone_base_stats(lightcone_id: str, ascension: int, level: int):
    data = _lightcone_ascension_data[lightcone_id]["values"]
    return stats.Stats(*[_str_base_stat_map[stat](base_step["base"] + base_step["step"] * (level - 1)) for stat, base_step in data[ascension].items()])


def get_lightcone_data(id: str, superimposition: int):
    return _lightcone_superimposition_data[id]["params"][superimposition - 1]
