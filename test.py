import console
import hsr
from hsr import characters, enemies, events, lightcones, multipiers


def event_print(event: hsr.Event):
    pass


def damage_print(event: events.EventDamage):
    output = []
    output.append(f"{event.damage.__class__.__name__}:")
    output.append(getattr(event.damage.source, "name") if hasattr(event.damage.source, "name") else event.damage.source.__class__.__name__)
    output.append(event.damage.source_unit.name)
    output.append(f"{event.damage.calc():.0f}")
    if (cm := event.damage.get_multipier(multipiers.CritMultipier)) and cm.crit:
        output.append("CRIT!")
    output.append(event.damage.target_unit.name)
    print(*output)


def node_print(event: events.EventNodeStart):
    if isinstance(event.node, hsr.UnitNode):
        print("Node:", event.node.__class__.__name__, event.node.unit.name)
    elif isinstance(event.node, hsr.Action):
        if hsr.ActionFlag.attack in event.node.flag:
            pass
        elif isinstance(event.node, hsr.WeakAction):
            print(f"WeakAction:", event.node.name, event.node.unit.name)
        else:
            print(f"Action:", event.node.name, event.node.unit.name)
    else:
        print("Node:", event.node.__class__.__name__)


def attack_print(event: events.EventActionEnd):
    if hsr.ActionFlag.attack not in event.action.flag:
        return
    print(f"Attack: [{event.action.name}] {event.action.unit.name} -> {', '.join(target.name for target in event.action.targets)}")


def over_turn_action_select(event: events.EventActionEnd):
    hsr.OverTurn(event.action.unit).chain()


def actor_indicator_add(event: events.EventTurn):
    console.ActorIndicator(event.unit).add()


def actor_indicator_remove(event: events.EventTurnEnd):
    if (indicator := event.unit.get_mod(console.ActorIndicator)) is not None:
        indicator.remove()


controller = console.ConsoleController()


def setup_test(event: events.EventEnterBattle):
    # event.unit.stats += hsr.Stats(HP(increase=10.0, exclusive_flag=hsr.stats.ConvertFlag.convert))
    event.unit.status[hsr.stats.HP] = event.unit.stats[hsr.stats.HP]
    event.unit.status[hsr.stats.Energy] = 0.5 * event.unit.stats[hsr.stats.Energy]
    console.init_indicators(event.unit)
    if not isinstance(event.unit, enemies.Enemy):
        hsr.ActionSelector(controller, event.unit).add()


def main():
    battle1 = hsr.Battle()
    team1 = hsr.Team(battle1)
    team2 = hsr.Team(battle1)
    team2.add()
    team1.add()
    qq = characters.Qingque(team1)
    lightcones.GeniusesRepose(qq).add()
    qq.add()
    rmc = characters.RMC(team1)
    lightcones.VictoryInABlink(rmc).add()
    rmc.add()
    for i in range(4):
        dm = enemies.Dummy(team2)
        dm.add()
        dm.name += f"-{i+1}"
    battle1.start()
    for unit in battle1.turn():
        hsr.Turn(unit).chain()


hsr.listen(hsr.Event, event_print)
hsr.listen(events.EventDamage, damage_print, hsr.Priority.Event.damage_print)
hsr.listen(events.EventNodeStart, node_print)
hsr.listen(events.EventActionEnd, attack_print)
hsr.listen(events.EventActionEnd, over_turn_action_select, hsr.Priority.Event.over_turn)
hsr.listen(events.EventTurn, actor_indicator_add)
hsr.listen(events.EventTurnEnd, actor_indicator_remove)
hsr.listen(events.EventEnterBattle, setup_test)
main()
