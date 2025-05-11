from game import Action, ActionFlag, ActionProvider, ActionSelector, BounceAction, Controller, Source, SourcelessMod, Team, Unit, listen
from game.events import EventAction, EventEnterBattle, EventStatusChange, EventTurn
from game.stats import *
from game.stats import Stats

from ..buff import Buff, TickType
from ..data.characters import rmc as data
from ..debuffs import Control
from ..events import EventDamage, EventDeath
from ..multipiers import MaxHPPercentMultipier
from ..priority import Priority
from ..statusmanager import Damage, DamageFlag, Heal, HealFlag, TrueDamage, deal_damage, regenerate_energy
from ..ult import UltActivator
from .character import Character, Memosprite, MemospriteTracer, RemembranceCharacter


class Mem(Memosprite):
    def __init__(self, stats: Stats, master: RemembranceCharacter) -> None:
        super().__init__("Mem", "Mem", stats, master.team, master)
        self.energy = 0.0
        self.accumulated = 0.0
        MemActionProvider(self, self, False).add()
        ForceAttackSelector(self).add()

    def add(self, index=-1):
        self.listener = listen(EventStatusChange, self.on_status_change)
        self.listener2 = listen(EventEnterBattle, self.on_enter_battle)
        self.listener3 = listen(EventDeath, self.on_death)
        for ally in self.team.units:
            FriendsTogether(self, ally).apply()
        self.regenerate_energy(data.mem_talent_energy[self.master.memosprite_talent_level - 1])
        index = self.team.units.index(self.master) + 1
        super().add(index)
        if self.master.check_trace(1) and not self.master.get_mod(Trace1Trigged):
            self.regenerate_energy(data.t1_energy)
            Trace1Trigged(self.master).add()

    def remove(self):
        self.listener.remove()
        self.listener2.remove()
        self.listener3.remove()
        for ally in self.team.units:
            for buff in ally.get_mods(FriendsTogether):
                buff.remove()
        self.master.action_advance(data.mem_talent_advance[self.master.memosprite_talent_level - 1])
        return super().remove()

    def add_tracer(self):
        MemTracer(self.master, self).add()

    def on_status_change(self, event: EventStatusChange[Energy, float]):
        if event.unit.team is not self.team:
            return
        if event.stat_type is not Energy:
            return
        if event.current <= event.previous:
            return
        delta = event.current - event.previous
        self.accumulated += delta
        self.regenerate_energy(self.accumulated // data.talent_energy_per[self.master.talent_level - 1] * 0.01)
        self.accumulated %= data.talent_energy_per[self.master.talent_level - 1]

    def on_enter_battle(self, event: EventEnterBattle):
        if event.unit.team is not self.team:
            return
        FriendsTogether(self, event.unit).apply()

    def on_death(self, event: EventDeath):
        if event.node.unit is not self.master:
            return
        self.status[HP, self] = 0

    def regenerate_energy(self, amount: float):
        if amount <= 0:
            return
        self.energy += amount
        if self.energy >= 1.0:
            self.energy = 1.0
            self.action_advance(self.runner_data.distance)
            for force_attack in self.get_mods(ForceAttackSelector):
                force_attack.remove()
        else:
            if not self.get_mod(ForceAttackSelector):
                ForceAttackSelector(self).add()


class MemTracer(MemospriteTracer):
    @property
    def mem(self):
        mem = self.sprite
        assert isinstance(mem, Mem)
        return mem


class BaddiesTrouble(BounceAction):
    def __init__(self, unit: Memosprite) -> None:
        super().__init__("Baddies! Trouble!", unit, ActionFlag.attack | ActionFlag.bounce | ActionFlag.aoe)
        self.bounce_scale = data.mem_basic_bounce_scale[unit.master.memosprite_skill_level - 1]
        self.aoe_scale = data.mem_basic_aoe_scale[unit.master.memosprite_skill_level - 1]

    @property
    def mem(self):
        mem = self.unit
        assert isinstance(mem, Mem)
        return mem

    def run(self):
        for _ in range(data.mem_basic_bounce_count[self.mem.master.memosprite_skill_level - 1]):
            target = self.bounce()
            deal_damage(self, self.unit, target, self.bounce_scale, 5, self.flag | ElementFlag.ice)
            regenerate_energy(self, self.mem.master, 2, True)
        for target in self.unit.select_enemies():
            self.add_target(target)
            deal_damage(self, self.unit, target, self.aoe_scale, 10, self.flag | ElementFlag.ice)
            regenerate_energy(self, self.mem.master, 2, True)
        if self.mem.master.check_trace(2):
            self.mem.regenerate_energy(data.t2_energy)


class FriendsTogether(Buff):
    def __init__(self, source: Mem, unit: Unit) -> None:
        super().__init__(source, "Friends! Together!", unit, 0, TickType.none, False)
        self.converted_cd = data.mem_talent_convert_cd[source.master.memosprite_talent_level - 1]
        self.fixed_cd = data.mem_talent_flat_cd[source.master.memosprite_talent_level - 1]
        crit_dmg = CRIT_DMG(exclusive_flag=ConvertFlag.convert)
        crit_dmg.get_value = self.crit_damage_value
        self.stats = Stats(crit_dmg)

    def crit_damage_value(self):
        assert isinstance(self.source, Mem)
        return self.source.stats.get(CRIT_DMG, exclusive_flag=ConvertFlag.convert) * self.converted_cd + self.fixed_cd

    def add(self):
        self.unit.stats += self.stats
        return super().add()

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()


class MemsSupport(Buff):
    def __init__(self, source: Source | None, unit: Unit) -> None:
        if isinstance(source, MemsSupport):
            super().__init__(source, "Mem's Support", unit, 0, TickType.none)
            self.base_scale = source.base_scale
            self.trace3_enabled = source.trace3_enabled
            self.eidolon1_enabled = source.eidolon1_enabled
            self.eidolon4_enabled = source.eidolon4_enabled
            self.is_copy = True
            self.rmc = source.rmc
        else:
            super().__init__(source, "Mem's Support", unit, 3, TickType.start_end)
            mem = self.get_source(Mem)
            assert mem is not None
            self.base_scale = data.mem_skill_scale[mem.master.memosprite_skill_level - 1]
            self.trace3_enabled = mem.master.check_trace(3)
            self.eidolon1_enabled = mem.master.check_eidolon(1)
            self.eidolon4_enabled = mem.master.check_eidolon(4)
            self.is_copy = False
            self.rmc = mem.master
        self.copy_buffs: list[MemsSupport] = []

    @property
    def scale(self):
        if self.trace3_enabled:
            if self.eidolon4_enabled and self.unit.stats[Energy] == 0:
                return self.base_scale + data.e4_true_dmg_scale
            if self.unit.stats[Energy] > data.t3_energy_exceed:
                return min((self.unit.stats[Energy] - data.t3_energy_exceed) // data.t3_energy_per * data.t3_true_dmg_scale, data.t3_true_dmg_scale_max) + self.base_scale
        return self.base_scale

    def add(self):
        self.listener = listen(EventStatusChange, self.on_status_change, Priority.Event.true_damage)
        self.listener2 = listen(EventEnterBattle, self.on_enter_battle)
        self.stats = Stats(CRIT_Rate(data.e1_dmg_crit)) if self.eidolon1_enabled else Stats()
        self.unit.stats += self.stats
        if self.is_copy:
            assert isinstance(self.source, MemsSupport)
            self.source.copy_buffs.append(self)
        else:
            for buff in self.unit.get_mods(MemsSupport):
                if buff.rmc is self.rmc:
                    buff.remove()
            if self.eidolon1_enabled:
                if isinstance(self.unit, RemembranceCharacter):
                    for tracer in self.unit.get_mods(MemospriteTracer):
                        MemsSupport(self, tracer.sprite).apply()
                elif isinstance(self.unit, Memosprite):
                    MemsSupport(self, self.unit.master).apply()
        return super().add()

    def remove(self):
        self.listener.remove()
        self.listener2.remove()
        self.unit.stats -= self.stats
        for copy in self.copy_buffs:
            if copy._keep_ref is None:  # already removed
                continue
            copy.remove()
        super().remove()
        if not self.is_copy:  # check if both the master and memosprite have the original version buff
            friends: list[Unit] = []
            if isinstance(self.unit, RemembranceCharacter):
                for tracer in self.unit.get_mods(MemospriteTracer):
                    friends.append(tracer.sprite)
            elif isinstance(self.unit, Memosprite):
                friends.append(self.unit.master)
            for friend in friends:
                for buff in friend.get_mods(MemsSupport):
                    if not buff.is_copy and buff.rmc is self.rmc:
                        MemsSupport(buff, self.unit).apply()
                        break
                else:
                    continue
                break
        del self.rmc

    def on_status_change(self, event: EventStatusChange[HP, float]):
        if event.stat_type is not HP:
            return
        if not isinstance(event.source, Damage):
            return
        if event.source.source_unit is not self.unit:
            return
        if isinstance(event.source, TrueDamage):
            return
        TrueDamage(self, self.unit, event.source.target_unit, event.source.calc() * self.scale, None).deal()

    def on_enter_battle(self, event: EventEnterBattle):
        if not self.eidolon1_enabled:
            return
        if self.is_copy:
            return
        if not isinstance(event.unit, Memosprite):
            return
        if event.unit.master is not self.unit:
            return
        MemsSupport(self, event.unit).apply()

    def get_stack_buff(self):
        for buff in self.unit.get_mods(type(self)):
            if buff.rmc is self.rmc and (self.is_copy or not buff.is_copy):
                return buff


class LemmeHelpYou(Action):
    def __init__(self, unit: Unit, target: Unit) -> None:
        super().__init__("Lemme! Help You!", unit, ActionFlag.single)
        self.main_target = target
        self.context["hotkey"] = "E"

    @property
    def mem(self):
        mem = self.unit
        assert isinstance(mem, Mem)
        return mem

    def run(self):
        self.mem.energy = 0.0
        assert self.main_target is not None
        self.add_target(self.main_target)
        regenerate_energy(self, self.mem.master, 10, True)
        if self.main_target is not self.unit:
            self.main_target.action_advance(10000)
        MemsSupport(self, self.main_target).apply()


class RMC(RemembranceCharacter):
    def __init__(
        self,
        team: Team,
        ascension=6,
        level=80,
        basic_level=6,
        skill_level=10,
        ult_level=10,
        talent_level=10,
        memosprite_skill_level=6,
        memosprite_talent_level=6,
        eidolon_level=6,
        trace_flags: tuple[bool, ...] = (True,) * 3,
        trace_stats_flags: tuple[bool, ...] = (True,) * 10,
    ) -> None:
        super().__init__(
            "Trailblazer",
            "RMC",
            team,
            ascension,
            level,
            basic_level,
            skill_level,
            ult_level,
            talent_level,
            memosprite_skill_level,
            memosprite_talent_level,
            eidolon_level,
            trace_flags,
            trace_stats_flags,
        )
        self.e2_enabled = True
        RMCAP(self, self, False).add()
        UltActivator(self, RMCUltProvider(self, self, False)).add()

    def generate_base_stats(self, ascension: int, level: int) -> Stats:
        return data.generate_base_stats(ascension, level)

    def get_trace_stats(self, *trace_stats_flags: bool) -> Stats:
        return data.generate_trace_stats(*trace_stats_flags)

    def set_eidolon(self, e1: bool, e2: bool, e3: bool, e4: bool, e5: bool, e6: bool):
        if e3:
            self.skill_level += 2
            self.talent_level += 2
            self.memosprite_talent_level += 1
        if e5:
            self.ult_level += 2
            self.basic_level += 1
            self.memosprite_skill_level += 1
        return super().set_eidolon(e1, e2, e3, e4, e5, e6)

    def add(self, index=-1):
        self.listener = listen(EventTurn, self.on_turn)
        self.listener2 = listen(EventAction, self.on_action)
        self.listener3 = listen(EventDamage, self.on_damage)
        super().add(index)
        if self.check_trace(1):
            self.action_advance(data.t1_action_advance)

    def remove(self):
        self.listener.remove()
        self.listener2.remove()
        self.listener3.remove()
        return super().remove()

    def on_turn(self, event: EventTurn):
        if not self.check_eidolon(2):
            return
        if event.unit.team is not self.team:
            return
        if event.unit is self:
            self.e2_enabled = True
            return
        if not self.e2_enabled:
            return
        if not isinstance(event.unit, Memosprite):
            return
        if isinstance(event.unit, Mem):
            return
        self.e2_enabled = False
        regenerate_energy(self, self, data.e2_energy, True)

    def on_action(self, event: EventAction):
        if not self.check_eidolon(4):
            return
        if event.action.unit.team is not self.team:
            return
        if "in_turn" not in event.action.context:
            return
        if not isinstance(event.action.unit, Character):
            return
        if event.action.unit.stats[Energy] > 0:
            return
        if (mem_tracer := self.get_mod(MemTracer)) is None:
            return
        mem_tracer.mem.regenerate_energy(data.e4_mem_energy)

    def on_damage(self, event: EventDamage):
        if not self.check_eidolon(6):
            return
        if not isinstance(event.damage.source, Ult):
            return
        if not isinstance(event.damage.source_unit, Mem):
            return
        if event.damage.source_unit.master is not self:
            return
        event.damage.source_stats.locks.append(CRIT_Rate(data.e6_crit_rate))

    def generate_memosprite_stats(self):
        return Stats(
            HP(self.stats.get_stat(HP, exclusive_flag=ConvertFlag.convert).get_base() * data.talent_hp_percent[self.talent_level - 1], flat=data.talent_hp_flat[self.talent_level - 1]),
            ATK(self.stats.get_stat(ATK, exclusive_flag=ConvertFlag.convert).get_base()),
            DEF(self.stats.get_stat(DEF, exclusive_flag=ConvertFlag.convert).get_base()),
            SPD(130),
            Aggro(100),
            CRIT_Rate(0.05),
            CRIT_DMG(0.5),
            Energy(0),
            Level(self.stats[Level]),
        )


class Basic(Action):
    def __init__(self, unit: Character, target: Unit) -> None:
        super().__init__("Leave It to Me!", unit, ActionFlag.attack | ActionFlag.basic | ActionFlag.single)
        self.main_target = target
        self.scale = data.basic_scale[unit.basic_level - 1]

    def run(self):
        assert self.main_target is not None
        self.unit.team.gain_skill_point(self, 1)
        self.add_target(self.main_target)
        deal_damage(self, self.unit, self.main_target, self.scale, 10, self.flag | ElementFlag.ice)
        regenerate_energy(self, self.unit, 20, True)


class Skill(Action):
    def __init__(self, unit: Character) -> None:
        super().__init__("I Choose You!", unit, ActionFlag.skill | ActionFlag.single)
        self.main_target = unit
        self.heal_percent = data.skill_heal[unit.skill_level - 1]
        self.energy_regenerate = data.skill_energy[unit.skill_level - 1]

    def run(self):
        assert isinstance(self.unit, RMC)
        self.unit.team.cost_skill_point(self, 1)
        self.add_target(self.unit)
        if mem_tracer := self.unit.get_mod(MemTracer):
            mem = mem_tracer.mem
            for control in mem.get_mods(Control):
                control.dispel(self)
            Heal(self, self.unit, mem, self.flag, MaxHPPercentMultipier(self.heal_percent)).deal()
            mem.regenerate_energy(self.energy_regenerate)
        else:
            mem = Mem(self.unit.generate_memosprite_stats(), self.unit)
            mem.add()
        regenerate_energy(self, self.unit, 30, True)


class Ult(Action):
    def __init__(self, unit: Character) -> None:
        super().__init__("Together, Mem!", unit, ActionFlag.aoe | ActionFlag.attack | ActionFlag.ult)
        self.scale = data.ult_scale[unit.ult_level - 1]
        self.energy_regenerate = data.ult_energy[unit.ult_level - 1]

    def run(self):
        assert isinstance(self.unit, RMC)
        self.unit.status[Energy, self] -= 160
        if mem_tracer := self.unit.get_mod(MemTracer):
            mem = mem_tracer.mem
            for control in mem.get_mods(Control):
                control.dispel(self)
        else:
            mem = Mem(self.unit.generate_memosprite_stats(), self.unit)
            mem.add()
        mem.regenerate_energy(self.energy_regenerate)
        for enemy in mem.select_enemies():
            self.add_target(enemy)
            deal_damage(self, mem, enemy, self.scale, 20, self.flag | ElementFlag.ice)
        regenerate_energy(self, self.unit, 5, True)


class Trace1Trigged(SourcelessMod):
    pass


class RMCAP(ActionProvider):
    def get_available_actions(self) -> list[Action]:
        assert isinstance(self.unit, Character)
        available_actions: list[Action] = []
        available_actions.extend(Basic(self.unit, enemy) for enemy in self.unit.select_enemies())
        if self.unit.team.skill_point > 0:
            available_actions.append(Skill(self.unit))
        return available_actions


class RMCUltProvider(ActionProvider):
    def get_available_actions(self) -> list[Action]:
        assert isinstance(self.unit, Character)
        return [Ult(self.unit)]


class MemActionProvider(ActionProvider):
    def get_available_actions(self) -> list[Action]:
        assert isinstance(self.unit, Mem)
        if self.unit.energy < 1:
            return [BaddiesTrouble(self.unit)]
        else:
            return [LemmeHelpYou(self.unit, ally) for ally in self.unit.select_allies()]


class ForceAttackSelector(ActionSelector):
    def __init__(self, unit: Unit) -> None:
        super().__init__(ForceAttackController(), unit, -1)


class ForceAttackController(Controller):
    def choose_action(self, actions: list[Action], allow_skip=False) -> Action | None:
        if len(actions) > 0:
            return actions[0]
        return None
