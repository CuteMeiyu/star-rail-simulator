import random

from hsrgame.action import Action, ActionFlag, ActionProvider, WeakAction
from hsrgame.buff import Buff, TickType
from hsrgame.combat import EventBattleStart, EventTurn, Mod, Team, Unit
from hsrgame.damage import Damage, DamageFlag, EventDamage, ToughnessDamage
from hsrgame.event import listen
from hsrgame.source import Source
from hsrgame.stats import *

from ...character import Character, EventUnitReady, Turn
from ...data.characters import qingque as data
from ...priority import Priority


class Qingque(Character):
    def __init__(self, stats: Stats, team: Team, basic_level=6, skill_level=10, ult_level=10, talent_level=10, eidolon_level=0, trace_level=3) -> None:
        super().__init__("Qingque", "QQ", stats, team, basic_level, skill_level, ult_level, talent_level, eidolon_level, trace_level)
        Passive(self).add()


class HiddenHand(Buff):
    def __init__(self, source: Source | None, unit: Character) -> None:
        super().__init__(source, "Hidden Hand", unit, 1, DebuffFlag(), TickType.end)
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
        self.pool = ["Wan", "Tong", "Tiao"]
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

    def draw(self, n=1, pool: list[str] | None = None):
        assert isinstance(self.unit, Character)
        if self.unit.check_eidolon(2):
            self.unit.regenerate_energy(self, 1, False)
        if pool is None:
            pool = self.pool
        self.performed = False
        self.tiles.extend(random.choices(pool, k=n))
        self.tiles.sort(key=lambda x: (-self.tiles.count(x), self.tiles.index(x)))
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
        self.draw(4, ["Yu"])

    def on_turn_start(self, event: EventTurn):
        if event.unit.team is not self.unit.team:
            return
        if self.is_win():
            return
        self.draw(1)

    def on_unit_ready(self, event: EventUnitReady):
        if event.unit is not self.unit:
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
        self.unit.team.change_skill_point(self, 1)
        passive = self.unit.get_mod(Passive)
        if passive is not None:
            passive.pop()
        self.add_target(self.main_target)
        ToughnessDamage(self, self.unit, self.main_target, 10, CombatType.quantum).deal()
        Damage(self, self.unit, self.main_target, self.scale, DamageFlag.basic, CombatType.quantum).deal()
        self.unit.regenerate_energy(self, 20, False)
        if self.unit.get_mod(AutarkyBuff):
            Autarky(self, self.unit, self.main_target).chain()


class WinningHand(Buff):
    def __init__(self, source: Source | None, unit: Unit) -> None:
        super().__init__(source, "Winning Hand", unit, 1, DebuffFlag(), TickType.start_end)
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
        for adjacent in self.unit.get_adjacent():
            self.add_target(adjacent)
        ToughnessDamage(self, self.unit, self.main_target, 20, CombatType.quantum).deal()
        Damage(self, self.unit, self.main_target, self.main_scale, DamageFlag.basic, CombatType.quantum).deal()
        for target in self.minor_targets:
            ToughnessDamage(self, self.unit, target, 10, CombatType.quantum).deal()
            Damage(self, self.unit, target, self.minor_scale, DamageFlag.basic, CombatType.quantum).deal()
        self.unit.regenerate_energy(self, 20, False)
        hidden_hand = self.unit.get_mod(HiddenHand)
        if hidden_hand is not None:
            hidden_hand.remove()
        if self.unit.check_trace(3):
            WinningHand(self, self.unit).add()
        if self.unit.get_mod(AutarkyBuff):
            EnhausedAutarky(self, self.unit, self.main_target).chain()
        if self.unit.check_eidolon(6):
            self.unit.team.change_skill_point(self, 1)


class AScoopOfMoon(Buff):
    def __init__(self, skill: "Skill", unit: Unit) -> None:
        super().__init__(skill, "A Scoop of Moon", unit, 1, DebuffFlag(), TickType.end, max_stack=4)
        self.dmg_boost = DMG_Boost(skill.dmg_boost)
        self.stats = Stats(self.dmg_boost)

    def add(self):
        self.unit.stats += self.stats
        return super().add()

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()

    def stack(self, amount=1):
        super().stack(amount)
        assert isinstance(self.source, Skill)
        self.dmg_boost.value = self.source.dmg_boost * self.stacks


class ExtraTurn(Turn):
    pass


class AutarkyBuff(Buff):
    def __init__(self, source: Source | None, unit: Unit) -> None:
        super().__init__(source, "Autarky", unit, 1, DebuffFlag(), TickType.end, False)


class Autarky(Action):
    def __init__(self, bind: Basic, unit: Unit, target: Unit) -> None:
        super().__init__("Autarky", unit, ActionFlag.attack | ActionFlag.follow_up | ActionFlag.single)
        self.main_target = target
        self.bind = bind

    def condition(self):
        return super().condition() and self.main_target is not None and self.main_target.selectable

    def run(self):
        assert self.main_target is not None
        self.add_target(self.main_target)
        ToughnessDamage(self, self.unit, self.main_target, 10, CombatType.quantum).deal()
        Damage(self, self.unit, self.main_target, self.bind.scale, DamageFlag.follow_up, CombatType.quantum).deal()


class EnhausedAutarky(Action):
    def __init__(self, bind: EnhausedBasic, unit: Unit, target: Unit) -> None:
        super().__init__("Autarky", unit, ActionFlag.attack | ActionFlag.follow_up | ActionFlag.blast)
        self.main_target = target
        self.bind = bind

    def condition(self):
        return super().condition() and self.main_target is not None and self.main_target.selectable

    def run(self):
        assert self.main_target is not None
        self.add_target(self.main_target)
        for adjacent in self.unit.get_adjacent():
            self.add_target(adjacent)
        ToughnessDamage(self, self.unit, self.main_target, 20, CombatType.quantum).deal()
        Damage(self, self.unit, self.main_target, self.bind.main_scale, DamageFlag.follow_up, CombatType.quantum).deal()
        for target in self.minor_targets:
            ToughnessDamage(self, self.unit, target, 10, CombatType.quantum).deal()
            Damage(self, self.unit, target, self.bind.minor_scale, DamageFlag.follow_up, CombatType.quantum).deal()


class Skill(Action):
    def __init__(self, unit: Character) -> None:
        super().__init__("A Scoop of Moon", unit, ActionFlag.single | ActionFlag.skill)
        self.main_target = unit
        self.dmg_boost = data.skill_dmg_boost[unit.skill_level - 1]
        if unit.check_trace(2):
            self.dmg_boost += 0.1

    def run(self):
        assert isinstance(self.unit, Character)
        self.unit.team.change_skill_point(self, -1)
        if self.unit.check_trace(1) and not self.unit.get_mod(Trace1Trigged):
            self.unit.team.change_skill_point(self, 1)
            Trace1Trigged(self.unit).add()
        self.add_target(self.unit)
        passive = self.unit.get_mod(Passive)
        if passive is not None:
            passive.draw(2)
        buff = self.unit.get_mod(AScoopOfMoon)
        if buff is None:
            AScoopOfMoon(self, self.unit).add()
        else:
            buff.stack()
        ExtraTurn(self.unit).chain()
        if self.unit.check_eidolon(4) and random.random() < 0.24 and not self.unit.get_mod(AutarkyBuff):
            AutarkyBuff(self, self.unit).add()


class Ult(Action):
    def __init__(self, unit: Character, enemy_team: Team) -> None:
        super().__init__("A Quartet? Woo-hoo!", unit, ActionFlag.aoe | ActionFlag.attack | ActionFlag.ult)
        self.enemy_team = enemy_team
        self.scale = data.ult_scale[unit.ult_level - 1]

    def run(self):
        assert isinstance(self.unit, Character)
        self.unit.cost_energy(self, 140)
        for enemy in self.enemy_team.get_units():
            self.add_target(enemy)
        for target in self.targets:
            ToughnessDamage(self, self.unit, target, 20, CombatType.quantum).deal()
            Damage(self, self.unit, target, self.scale, DamageFlag.ult, CombatType.quantum)
        self.unit.regenerate_energy(self, 5, False)
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
