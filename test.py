import console
import game
import hsr
from game.events import EventActionEnd, EventEnterBattle, EventNodeStart, EventTurn, EventTurnEnd
from game.stats import HP, Energy
from hsr import characters, enemies, multipiers
from hsr.events import EventDamage


def event_print(event: game.Event):
    pass


def damage_print(event: EventDamage):
    output = []
    output.append(f"{event.damage.__class__.__name__}:")
    output.append(getattr(event.damage.source, "name") if hasattr(event.damage.source, "name") else event.damage.source.__class__.__name__)
    output.append(event.damage.unit.name)
    output.append(f"{event.damage.calc():.0f}")
    if (cm := event.damage.get_multipier(multipiers.CritMultipier)) and cm.crit:
        output.append("CRIT!")
    output.append(event.damage.target.name)
    print(*output)


def node_print(event: EventNodeStart):
    if isinstance(event.node, game.UnitNode):
        print("Node:", event.node.__class__.__name__, event.node.unit.name)
    elif isinstance(event.node, game.Action):
        if game.ActionFlag.attack in event.node.flag:
            pass
        elif isinstance(event.node, game.WeakAction):
            print(f"WeakAction:", event.node.name, event.node.unit.name)
        else:
            print(f"Action:", event.node.name, event.node.unit.name)
    else:
        print("Node:", event.node.__class__.__name__)


def attack_print(event: EventActionEnd):
    if game.ActionFlag.attack not in event.action.flag:
        return
    print(f"Attack: [{event.action.name}] {event.action.unit.name} -> {', '.join(target.name for target in event.action.targets)}")


def over_turn_action_select(event: EventActionEnd):
    hsr.OverTurn(event.action.unit).chain()


def actor_indicator_add(event: EventTurn):
    console.ActorIndicator(event.unit).add()


def actor_indicator_remove(event: EventTurnEnd):
    if (indicator := event.unit.get_mod(console.ActorIndicator)) is not None:
        indicator.remove()


controller = console.ConsoleController()


def setup_test(event: EventEnterBattle):
    # event.unit.stats += game.Stats(HP(increase=10.0, exclusive_flag=game.stats.ConvertFlag.convert))
    event.unit.status[HP] = event.unit.stats[HP]
    event.unit.status[Energy] = 0.5 * event.unit.stats[Energy]
    console.init_indicators(event.unit)
    if not isinstance(event.unit, enemies.Enemy):
        game.ActionSelector(controller, event.unit).add()


def main():
    battle1 = game.Battle()
    team1 = game.Team(battle1)
    team2 = game.Team(battle1)
    team2.add()
    team1.add()
    characters.Qingque(team1).add()
    characters.RMC(team1).add()
    for i in range(4):
        dm = enemies.Dummy(team2)
        dm.add()
        dm.name += f"-{i+1}"
    battle1.start()
    for unit in battle1.turn():
        hsr.Turn(unit).chain()


game.listen(game.Event, event_print)
game.listen(EventDamage, damage_print, hsr.Priority.Event.last)
game.listen(EventNodeStart, node_print)
game.listen(EventActionEnd, attack_print)
game.listen(EventActionEnd, over_turn_action_select, hsr.Priority.Event.first)
game.listen(EventTurn, actor_indicator_add)
game.listen(EventTurnEnd, actor_indicator_remove)
game.listen(EventEnterBattle, setup_test)
main()
