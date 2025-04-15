from game.action import Action, ActionFlag, Controller, ControllerGroup, EventActionEnd
from game.combat import Battle, BattlePhase, EventNodeStart, Team, Unit
from game.event import listen
from game.multipier import DamageCalculator, EventDamage, Multipier
from game.stats import Energy
from hsr.characters import *
from hsr.enemies import *
from hsr.hsr import Indicator, OverTurn, Turn, UltActivate
from hsr.priority import Priority


def on_node(event: EventNodeStart):
    if isinstance(event.node, Action):
        print(event.node.name, event.node.unit.name)
    else:
        print(event.node.__class__.__name__)


listen(EventNodeStart, on_node)


class ZeroDamageMultipier(Multipier[DamageCalculator]):
    def get(self) -> float:
        return 0.0


def on_damage(event: EventDamage):
    damage = event.damage
    calculator = damage.damage_calculator
    name = getattr(damage.source, "name") if hasattr(damage.source, "name") else damage.source.__class__.__name__
    print("Damage:", calculator.unit.name, name, calculator.target.name, calculator.calc())
    calculator.add_multipier(ZeroDamageMultipier(calculator))


listen(EventDamage, on_damage, Priority.Event.last)


def on_action_end(event: EventActionEnd):
    OverTurn(event.action.unit).chain()


listen(EventActionEnd, on_action_end, Priority.Event.first)


class CurrentActorIndicator(Indicator):
    def __init__(self, unit: Unit) -> None:
        super().__init__(None, unit)

    def modify_unit_string(self, unit_string: str) -> str:
        return f"[{unit_string}]"


def get_unit_string(unit: Unit):
    string = f"{unit.name}({'|'.join(indicator.string() for indicator in unit.get_mods(Indicator) if len(indicator.string()) > 0)})"
    for indicator in unit.get_mods(Indicator):
        string = indicator.modify_unit_string(string)
    return string


def get_team_string(team: Team, sep="\t"):
    return sep.join(get_unit_string(unit) for unit in team.units)


def print_battle(battle: Battle):
    print(battle.schedule)
    print(t1.skill_point)
    for team in battle.teams:
        print(get_team_string(team))


class ConsoleController(ControllerGroup):
    def choose_action(self, actions: list[Action], allow_skip=False) -> Action | None:
        if len(actions) == 0:
            return None
        print_battle(actions[0].unit.team.battle)
        cmd_dict: dict[str, Action | None] = {}
        for action in actions:
            cmd = ""
            if ActionFlag.basic in action.flag or ActionFlag.ult in action.flag:
                cmd += "Q"
            elif ActionFlag.skill in action.flag:
                cmd += "E"
            elif isinstance(action, UltActivate):
                cmd += str(action.unit.team.units.index(action.unit) + 1)
            if action.main_target is not None:
                cmd += str(action.main_target.team.units.index(action.main_target) + 1)
            cmd_dict[cmd] = action
        if allow_skip:
            cmd_dict["X"] = None
        print(*cmd_dict.keys())
        while True:
            cmd = input("Input Command: ").upper()
            if cmd in cmd_dict:
                break
            print("Invalid Command!")
        return cmd_dict[cmd]


cg1 = ConsoleController()
# cg2 = ConsoleController()
b1 = Battle()
t1 = Team(b1)
t2 = Team(b1)
t1.add()
t2.add()
for i in range(4):
    qq = Qingque(t1)
    qq.name += f"-{i+1}"
    qq.add()
    qq.status[Energy] = 0.5 * qq.stats[Energy]
    Controller(cg1, qq).add()
for i in range(3):
    dm = Dummy(t2)
    dm.name += f"-{i+1}"
    dm.add()
    # Controller(cg2, qq).add()
b1.start()
for phase, unit in b1.turn():
    if phase == BattlePhase.ready:
        CurrentActorIndicator(unit).add()
        Turn(unit).chain()
        b1.run_nodes()
        indicator = unit.get_mod(CurrentActorIndicator)
        if indicator is not None:
            indicator.remove()
        print()
