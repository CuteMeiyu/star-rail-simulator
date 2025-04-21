import console
import game
import hsr
from game.events import EventActionEnd, EventNodeStart, EventTurn, EventTurnEnd
from game.stats import Energy
from hsr import characters, enemies


def event_print(event: game.Event):
    pass


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


def main():
    controller = console.ConsoleController()
    battle1 = game.Battle()
    team1 = game.Team(battle1)
    team2 = game.Team(battle1)
    team2.add()
    team1.add()
    for i in range(4):
        qq = characters.Qingque(team1)
        qq.status[Energy] = 0.5 * qq.stats[Energy]
        console.init_indicators(qq)
        game.ActionSelector(controller, qq).add()
        qq.name += f"-{i+1}"
        qq.add()
    for i in range(4):
        dm = enemies.Dummy(team2)
        console.init_indicators(dm)
        dm.name += f"-{i+1}"
        dm.add()
    battle1.start()
    for unit in battle1.turn():
        hsr.Turn(unit).chain()


game.listen(game.Event, event_print)
game.listen(EventNodeStart, node_print)
game.listen(EventActionEnd, attack_print)
game.listen(EventActionEnd, over_turn_action_select, hsr.Priority.Event.first)
game.listen(EventTurn, actor_indicator_add)
game.listen(EventTurnEnd, actor_indicator_remove)
main()
