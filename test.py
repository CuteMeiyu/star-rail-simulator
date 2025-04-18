import console
import game
import hsr
from game.events import EventActionEnd, EventNodeStart
from game.stats import Energy
from hsr import characters, enemies
from hsr.events import EventDamage, EventToughnessDamage


def node_print(event: EventNodeStart):
    if isinstance(event.node, game.Action):
        if isinstance(event.node, (hsr.Turn, hsr.OverTurn)):
            print(f"{event.node.name}:", event.node.unit.name)
        elif isinstance(event.node, game.WeakAction):
            print("Node:", event.node.name, event.node.unit.name)
        elif game.ActionFlag.attack in event.node.flag:
            event.node.context["damage_dict"] = {}
        else:
            print("Action:", event.node.name)
    else:
        print("Node:", event.node.__class__.__name__)


def damage_print(event: EventActionEnd):
    if game.ActionFlag.attack in event.action.flag:
        attack = event.action.name
        source = event.action.unit.name
        damage_dict: dict[game.Unit, tuple[float, int]] = event.action.context["damage_dict"]
        target = ", ".join(f"{target.name}({damage_dict[target][0]:.2f}{"!" if damage_dict[target][1] else ""})" for target in event.action.targets)
        print(f"Attack: [{attack}] {source} -> {target}")


class ZeroMultipier(hsr.Multipier):
    def get(self) -> float:
        return 0.0


def damage_record(event: EventDamage | EventToughnessDamage):
    damage = event.damage
    if isinstance(event, EventToughnessDamage):
        damage.add_multipier(ZeroMultipier(damage))
        return
    action = damage.source
    if not isinstance(action, game.Action):
        return
    crit_multipier = damage.get_multipier(hsr.multipiers.CritMultipier)
    crit = False if crit_multipier is None else crit_multipier.is_crit()
    damage_dict: dict[game.Unit, tuple[float, int]] = action.context["damage_dict"]
    if damage.target not in damage_dict:
        damage_dict[damage.target] = (damage.calc(), crit)
    else:
        s_damage, s_crit = damage_dict[damage.target]
        damage_dict[damage.target] = (damage.calc() + s_damage, crit + s_crit)
    damage.add_multipier(ZeroMultipier(damage))


def over_turn_action_select(event: EventActionEnd):
    hsr.OverTurn(event.action.unit).chain()


def main():
    controller = console.ConsoleController()
    battle1 = game.Battle()
    team1 = game.Team(battle1)
    team2 = game.Team(battle1)
    team2.add()
    team1.add()
    for i in range(4):
        qq = characters.Qingque(team1)
        console.init_indicators(qq)
        game.ActionSelector(controller, qq).add()
        qq.name += f"-{i+1}"
        qq.add()
        qq.status[Energy] = 0.5 * qq.stats[Energy]
    for i in range(3):
        dm = enemies.Dummy(team2)
        console.init_indicators(dm)
        dm.name += f"-{i+1}"
        dm.add()
    battle1.start()
    for phase, unit in battle1.turn():
        if phase == game.BattlePhase.ready:
            console.ActorIndicator(unit).add()
            hsr.Turn(unit).chain()
            battle1.run_nodes()
            indicator = unit.get_mod(console.ActorIndicator)
            if indicator is not None:
                indicator.remove()
            print()


game.listen(EventNodeStart, node_print)
game.listen(EventDamage | EventToughnessDamage, damage_record, hsr.Priority.Event.last)
game.listen(EventActionEnd, damage_print, hsr.Priority.Event.first)
game.listen(EventActionEnd, over_turn_action_select, hsr.Priority.Event.first)
main()
