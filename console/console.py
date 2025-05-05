import math

from game import Action, ActionFlag, Battle, Controller, Mod, SourcelessMod, Team, Unit
from game.stats import *
from hsr import UltActivate


class Indicator(SourcelessMod):
    def decorate(self, string: str) -> str: ...


class Suffix(SourcelessMod):
    def string(self) -> str: ...


class NameIndicator(Indicator):
    def decorate(self, string: str) -> str:
        return self.unit.name


class SuffixIndicator(Indicator):
    def decorate(self, string: str) -> str:
        return f"{string}({'|'.join(x for suffix in self.unit.get_mods(Suffix) if len(x := suffix.string()) > 0)})"


class ActorIndicator(Indicator):
    def decorate(self, string: str) -> str:
        return f"[{string}]"


def get_unit_string(unit: Unit):
    result = ""
    for indicator in unit.get_mods(Indicator):
        result = indicator.decorate(result)
    return result


def get_team_string(team: Team, sep="\t"):
    return sep.join(get_unit_string(unit) for unit in team.units)


def print_battle(battle: Battle):
    print(battle.schedule)
    for team in battle.teams:
        print(get_team_string(team))


class ConsoleController(Controller):
    def choose_action(self, actions: list[Action], allow_skip=False) -> Action | None:
        if len(actions) == 0:
            return None
        print_battle(actions[0].unit.team.battle)
        code_target_action: dict[str, dict[str, Action]] = {}
        for action in actions:
            ability_code = ""
            if "hotkey" in action.context:
                ability_code += action.context["hotkey"]
            elif ActionFlag.basic in action.flag:
                ability_code += "A"
            elif ActionFlag.skill in action.flag:
                ability_code += "E"
            elif ActionFlag.ult in action.flag:
                ability_code += "Q"
            elif isinstance(action, UltActivate):
                ability_code += str(action.unit.team.units.index(action.unit) + 1)
            if action.main_target is not None:
                target = str(action.main_target.team.units.index(action.main_target) + 1)
            else:
                target = ""
            extra_index = 1
            while True:
                if extra_index > 1:
                    new_ac = ability_code + str(extra_index)
                else:
                    new_ac = ability_code
                if new_ac not in code_target_action:
                    ability_code = new_ac
                    code_target_action[ability_code] = {}
                    break
                if target not in code_target_action[ability_code]:
                    break
                extra_index += 1
            code_target_action[ability_code][target] = action
        cmd_dict: dict[str, Action | None] = {}
        for code, target in code_target_action.items():
            if len(target) == 1:
                cmd_dict[code] = list(target.values())[0]
                continue
            for index, action in target.items():
                cmd_dict[code + index] = action
        if allow_skip:
            cmd_dict["X"] = None
        print("Skill Point:", actions[0].unit.team.skill_point)
        while True:
            cmd = input(f"Input Command ({'|'.join(cmd_dict.keys())}): ").upper()
            if cmd in cmd_dict:
                break
            print("Invalid Command!")
        print("=" * 60)
        return cmd_dict[cmd]


class NumericSuffix(Suffix):
    def __init__(self, unit: Unit, format=".0f", priority=0) -> None:
        super().__init__(unit, priority)
        self.previous: float | None = None
        self.no_change = "{:" + format + "}"
        self.changed = "{:" + format + "}({:+" + format + "})"

    def get_value(self) -> float | int: ...
    def string(self) -> str:
        current = self.get_value()
        if self.previous is None:
            delta = 0.0
        else:
            delta = current - self.previous
        self.previous = current
        if math.isclose(delta, 0):
            return self.no_change.format(current)
        return self.changed.format(current, delta)


class StatusSuffix(NumericSuffix):
    def __init__(self, unit: Unit, stat_type: type[Stat], priority=0) -> None:
        super().__init__(unit, ".0f", priority)
        self.stat_type = stat_type

    def get_value(self) -> float | int:
        return self.unit.status[self.stat_type]


class ModSuffix(Suffix):
    table: dict[type[Mod], str] = {}

    def string(self) -> str:
        return "|".join(string for mod_type, string in self.table.items() if self.unit.get_mod(mod_type))
