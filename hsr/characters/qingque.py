import random

from game.action import Action, ActionFlag, ActionProvider, MainTargetCondition, WeakAction
from game.combat import EventBattleStart, EventTurn, Mod, Team, Unit
from game.event import listen
from game.source import Source
from game.stats import *

from ..buff import Buff, TickType
from ..data.characters import qingque as data
from ..events import EventDamage
from ..statusmanager import DamageFlag, deal_damage, regenerate_energy
from ..turn import EventUnitReady, Turn
from ..ult import UltActivator
from ..units import Character


class Qingque(Character):
    def __init__(
        self,
        team: Team,
        stats: Stats | None = None,
        basic_level=6,
        skill_level=10,
        ult_level=10,
        talent_level=10,
        eidolon_level=6,
        trace_level=3,
    ) -> None:
        if stats is None:
            stats = data.base_stats.deepcopy()
        super().__init__("Qingque", "QQ", stats, team, basic_level, skill_level, ult_level, talent_level, eidolon_level, trace_level)
        Passive(self).add()
        BasicSkillProvider(self).add()
        UltActivator(self, UltProvider(self)).add()


class HiddenHand(Buff):
    def __init__(self, source: Source | None, unit: Character) -> None:
        super().__init__(source, "Hidden Hand", unit, 1, TickType.end)
        self.stats = Stats(ATK(increase=data.talent_atk_boost[unit.talent_level - 1]))

    def add(self):
        self.unit.stats += self.stats
        return super().add()

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()


class HiddenHandAnimation(WeakAction):
    def __init__(self, unit: Unit) -> None:
        super().__init__("Hidden Hand", unit)


class Passive(Mod):
    def __init__(self, unit: Character) -> None:
        super().__init__(unit, unit)
        self.tiles = []
        self.pool = ["A", "B", "C"]
        self.performed = False

    def add(self):
        self.on_turn_start_listener = listen(EventTurn, self.on_turn_start)
        self.on_unit_ready_listener = listen(EventUnitReady, self.on_unit_ready)
        self.on_damage_listener = listen(EventDamage, self.on_damage)
        return super().add()

    def remove(self):
        self.on_turn_start_listener.remove()
        self.on_unit_ready_listener.remove()
        self.on_damage_listener.remove()
        return super().remove()

    def is_win(self):
        return len(self.tiles) > 0 and self.tiles.count(self.tiles[0]) == 4

    def draw(self, n=1, pool: list[str] | None = None, trigger_e2=True):
        assert isinstance(self.unit, Character)
        if self.unit.check_eidolon(2) and trigger_e2:
            regenerate_energy(self, self.unit, 1, True)
        if pool is None:
            pool = self.pool
        self.performed = False
        self.tiles.extend(random.choices(pool, k=n))
        self.tiles = sorted(self.tiles, key=lambda x: (-self.tiles.count(x), self.tiles.index(x)))
        self.tiles = self.tiles[:4]
        if self.is_win() and self.unit.get_mod(HiddenHand) is None:
            HiddenHand(self, self.unit).add()

    def pop(self):
        if len(self.tiles) == 0:
            return None
        return self.tiles.pop()

    def clear(self):
        self.tiles.clear()

    def cheat(self):
        self.draw(6, ["F"], False)

    def on_turn_start(self, event: EventTurn):
        if event.unit.team is not self.unit.team:
            return
        if self.is_win():
            return
        self.draw(1)

    def on_unit_ready(self, event: EventUnitReady):
        if event.unit is not self.unit:
            return
        if event.turn.priority <= self.priority:
            return
        if self.performed:
            return
        if not self.is_win():
            return
        self.performed = True
        HiddenHandAnimation(self.unit).chain()

    def on_damage(self, event: EventDamage):
        assert isinstance(self.unit, Character)
        if event.damage.unit is not self.unit:
            return
        if not isinstance(event.damage.source, Action):
            return
        if ActionFlag.ult not in event.damage.source.flag:
            return
        if not self.unit.check_eidolon(1):
            return
        event.damage.source_stats += Stats(DMG_Boost(0.1))


class Basic(Action):
    def __init__(self, unit: Character, target: Unit) -> None:
        super().__init__("Flower Pick", unit, ActionFlag.attack | ActionFlag.single | ActionFlag.basic)
        self.main_target = target
        self.scale = data.basic_scale[unit.basic_level - 1]

    def run(self):
        assert self.main_target is not None
        assert isinstance(self.unit, Character)
        self.unit.team.gain_skill_point(self, 1)
        passive = self.unit.get_mod(Passive)
        if passive is not None:
            passive.pop()
        self.add_target(self.main_target)
        deal_damage(self, self.unit, self.main_target, self.scale, 10, DamageFlag.basic, ElementFlag.quantum)
        regenerate_energy(self, self.unit, 20, True)
        if self.unit.get_mod(AutarkyBuff):
            Autarky(self, self.unit, self.main_target).chain()


class WinningHand(Buff):
    def __init__(self, source: Source | None, unit: Unit) -> None:
        super().__init__(source, "Winning Hand", unit, 1, TickType.start_end)
        self.stats = Stats(SPD(increase=0.1))

    def add(self):
        self.unit.stats += self.stats
        return super().add()

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()


class EnhausedBasic(Action):
    def __init__(self, unit: Character, target: Unit) -> None:
        super().__init__("Cherry on Top!", unit, ActionFlag.attack | ActionFlag.blast | ActionFlag.basic)
        self.main_target = target
        self.main_scale = data.enhaused_basic_main_scale[unit.basic_level - 1]
        self.minor_scale = data.enhaused_basic_minor_scale[unit.basic_level - 1]

    def run(self):
        assert self.main_target is not None
        assert isinstance(self.unit, Character)
        passive = self.unit.get_mod(Passive)
        if passive is not None:
            passive.clear()
        self.add_target(self.main_target)
        for adjacent in self.main_target.select_adjacents():
            self.add_target(adjacent)
        deal_damage(self, self.unit, self.main_target, self.main_scale, 20, DamageFlag.basic, ElementFlag.quantum)
        for target in self.minor_targets:
            deal_damage(self, self.unit, target, self.minor_scale, 10, DamageFlag.basic, ElementFlag.quantum)
        regenerate_energy(self, self.unit, 20, True)
        hidden_hand = self.unit.get_mod(HiddenHand)
        if hidden_hand is not None:
            hidden_hand.remove()
        if self.unit.check_trace(3):
            WinningHand(self, self.unit).add()
        if self.unit.get_mod(AutarkyBuff):
            EnhausedAutarky(self, self.unit, self.main_target).chain()
        if self.unit.check_eidolon(6):
            self.unit.team.gain_skill_point(self, 1)


class AScoopOfMoon(Buff):
    def __init__(self, skill: "Skill", unit: Unit) -> None:
        super().__init__(skill, "A Scoop of Moon", unit, 1, TickType.end, max_stack=4)
        self.skill = skill
        self.dmg_boost = DMG_Boost(skill.dmg_boost)
        self.stats = Stats(self.dmg_boost)

    def add(self):
        self.unit.stats += self.stats
        return super().add()

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()

    def set_stacks(self, stacks: int):
        super().set_stacks(stacks)
        self.dmg_boost.value = self.skill.dmg_boost * self.stacks


class ExtraTurn(Turn):
    def __init__(self, unit: Unit) -> None:
        super().__init__(unit)


class AutarkyBuff(Buff):
    def __init__(self, source: Source | None, unit: Unit) -> None:
        super().__init__(source, "Autarky", unit, 1, TickType.end, False)


class Autarky(Action):
    def __init__(self, bind: Basic, unit: Unit, target: Unit) -> None:
        super().__init__("Autarky", unit, ActionFlag.attack | ActionFlag.follow_up | ActionFlag.single)
        self.main_target = target
        self.bind = bind
        self.add_conditions(MainTargetCondition())

    def run(self):
        assert self.main_target is not None
        self.add_target(self.main_target)
        deal_damage(self, self.unit, self.main_target, self.bind.scale, 10, DamageFlag.follow_up, ElementFlag.quantum)


class EnhausedAutarky(Action):
    def __init__(self, bind: EnhausedBasic, unit: Unit, target: Unit) -> None:
        super().__init__("Autarky", unit, ActionFlag.attack | ActionFlag.follow_up | ActionFlag.blast)
        self.main_target = target
        self.bind = bind
        self.add_conditions(MainTargetCondition())

    def run(self):
        assert self.main_target is not None
        self.add_target(self.main_target)
        for adjacent in self.main_target.select_adjacents():
            self.add_target(adjacent)
        deal_damage(self, self.unit, self.main_target, self.bind.main_scale, 20, DamageFlag.follow_up, ElementFlag.quantum)
        for target in self.minor_targets:
            deal_damage(self, self.unit, target, self.bind.minor_scale, 10, DamageFlag.follow_up, ElementFlag.quantum)


class Skill(Action):
    def __init__(self, unit: Character) -> None:
        super().__init__("A Scoop of Moon", unit, ActionFlag.single | ActionFlag.skill)
        self.main_target = unit
        self.dmg_boost = data.skill_dmg_boost[unit.skill_level - 1]
        if unit.check_trace(2):
            self.dmg_boost += 0.1

    def run(self):
        assert isinstance(self.unit, Character)
        self.unit.team.cost_skill_point(self, 1)
        if self.unit.check_trace(1) and not self.unit.get_mod(Trace1Trigged):
            self.unit.team.gain_skill_point(self, 1)
            Trace1Trigged(self.unit).add()
        self.add_target(self.unit)
        passive = self.unit.get_mod(Passive)
        if passive is not None:
            passive.draw(2)
        AScoopOfMoon(self, self.unit).add()
        ExtraTurn(self.unit).chain()
        if self.unit.check_eidolon(4) and random.random() < 0.24 and not self.unit.get_mod(AutarkyBuff):
            AutarkyBuff(self, self.unit).add()


class Ult(Action):
    def __init__(self, unit: Character) -> None:
        super().__init__("A Quartet? Woo-hoo!", unit, ActionFlag.aoe | ActionFlag.attack | ActionFlag.ult)
        self.scale = data.ult_scale[unit.ult_level - 1]

    def run(self):
        assert isinstance(self.unit, Character)
        self.unit.status[Energy, self] -= 140
        for enemy in self.unit.select_enemies():
            self.add_target(enemy)
        for target in self.targets:
            deal_damage(self, self.unit, target, self.scale, 20, DamageFlag.ult, ElementFlag.quantum)
        regenerate_energy(self, self.unit, 5, True)
        passive = self.unit.get_mod(Passive)
        if passive is not None:
            passive.cheat()


class Technique(Mod):
    def __init__(self, unit: Unit) -> None:
        super().__init__(unit, unit)

    def add(self):
        self.on_battle_start_listener = listen(EventBattleStart, self.on_battle_start)
        return super().add()

    def remove(self):
        self.on_battle_start_listener.remove()
        return super().remove()

    def on_battle_start(self, event: EventBattleStart):
        if event.battle is not self.unit.team.battle:
            return
        passive = self.unit.get_mod(Passive)
        if passive is not None:
            passive.draw(2)
        self.remove()


class TraceStats(Mod):
    def __init__(self, unit: Unit) -> None:
        super().__init__(unit, unit)
        self.stats = Stats(
            ATK(increase=data.trace_atk_boost),
            DMG_Boost(data.trace_dmg_boost, ElementFlag.quantum),
            DEF(increase=data.trace_def_boost),
        )

    def add(self):
        self.unit.stats += self.stats
        return super().add()

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()


class Trace1Trigged(Mod):
    def __init__(self, unit: Unit) -> None:
        super().__init__(unit, unit)


class BasicSkillProvider(ActionProvider):
    def __init__(self, unit: Unit) -> None:
        super().__init__(unit, unit, False)

    def get_available_actions(self):
        assert isinstance(self.unit, Character)
        actions: list[Action] = []
        if self.unit.get_mod(HiddenHand):
            actions.extend(EnhausedBasic(self.unit, target) for target in self.unit.select_enemies())
        else:
            actions.extend(Basic(self.unit, target) for target in self.unit.select_enemies())
            if self.unit.team.skill_point > 0:
                actions.append(Skill(self.unit))
        return actions


class UltProvider(ActionProvider):
    def __init__(self, unit: Unit) -> None:
        super().__init__(unit, unit, False)

    def get_available_actions(self) -> list[Action]:
        assert isinstance(self.unit, Character)
        return [Ult(self.unit)]
