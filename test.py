from game.action import Action, ActionFlag, Controller, ControllerGroup
from game.combat import Battle, BattlePhase, EventNodeStart, Team
from game.event import listen
from game.multipier import DamageCalculator, EventDamage, Multipier
from hsr.character import OverTurn, Turn, UltActivate
from hsr.characters import *
from hsr.priority import Priority


def on_node(event: EventNodeStart):
    if isinstance(event.node, Action):
        print(team1.skill_point, team2.skill_point)
        print(event.node.__class__.__name__, event.node.unit.name)
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


class ConsoleController(ControllerGroup):
    def choose_action(self, actions: list[Action], allow_skip=False) -> Action | None:
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
        print(cmd_dict.keys())
        cmd = input("Input Command: ")
        return cmd_dict[cmd]


cg1 = ConsoleController()
cg2 = ConsoleController()
battle = Battle()
team1 = Team(battle)
team2 = Team(battle)
team1.add()
team2.add()
for i in range(4):
    qq = Qingque(team1)
    qq.name += f"-1-{i+1}"
    qq.add()
    Controller(cg1, qq).add()
for i in range(4):
    qq = Qingque(team2)
    qq.name += f"-2-{i+1}"
    qq.add()
    Controller(cg2, qq).add()
for phase, unit in battle.turn():
    print(battle.schedule)
    if phase == BattlePhase.ready:
        Turn(unit).chain()
        battle.run_nodes()
        print()
    else:
        OverTurn(unit).chain()
        battle.run_nodes()
