from game import Action, ActionFlag, ActionProvider, ActionSelector, BounceAction, Controller, Source, SourcelessMod, Team, Unit, listen
from game.events import EventAction, EventEnterBattle, EventStatusChange, EventTurn
from game.stats import *

from ..buff import Buff, TickType
from ..data.characters import rmc as data
from ..debuffs import Control
from ..events import EventDamage
from ..multipiers import MaxHPPercentMultipier
from ..priority import Priority
from ..statusmanager import DamageFlag, Heal, HealFlag, TrueDamage, deal_damage, regenerate_energy
from ..ult import UltActivator
from ..units import Character, Memosprite, MemospriteTracer, RemembranceCharacter


class Mem(Memosprite):
    def __init__(self, stats: Stats, master: RemembranceCharacter) -> None:
        super().__init__("Mem", "Mem", stats, master.team, master)
        self.energy = 0.0
        self.accumulated = 0.0
        MemActionProvider(self, self, False).add()
        ForceAttack(self).add()

    def regenerate_energy(self, amount: float):
        if amount <= 0:
            return
        self.energy += amount
        if self.energy >= 1.0:
            self.energy = 1.0
            self.action_advance(self.runner_data.distance)
            for fa in self.get_mods(ForceAttack):
                fa.remove()
        else:
            if not self.get_mod(ForceAttack):
                ForceAttack(self).add()

    def add(self, index=-1):
        self.tracer = MemTracer(self.master, self)
        self.tracer.add()
        self.listener = listen(EventStatusChange, self.on_status_change)
        self.listener2 = listen(EventEnterBattle, self.on_enter_battle)
        for ally in self.team.units:
            FriendsTogether(self, ally).add()
        self.regenerate_energy(0.5)
        index = self.team.units.index(self.master) + 1
        super().add(index)
        if self.master.check_trace(1) and not self.master.get_mod(Trace1Trigged):
            self.regenerate_energy(data.t1_energy)
            Trace1Trigged(self.master).add()

    def remove(self):
        self.tracer.remove()
        self.listener.remove()
        self.listener2.remove()
        self.master.action_advance(2500)
        return super().remove()

    def on_status_change(self, event: EventStatusChange[Energy, float]):
        if event.unit.team is not self.team:
            return
        if event.stat_type is not Energy:
            return
        if event.current <= event.previous:
            return
        delta = event.current - event.previous
        self.accumulated += delta
        self.regenerate_energy(self.accumulated // 10 * 0.01)
        self.accumulated %= 10

    def on_enter_battle(self, event: EventEnterBattle):
        if event.unit.team is not self.team:
            return
        FriendsTogether(self, event.unit).add()


class MemTracer(MemospriteTracer[Mem]):
    pass


class BaddiesTrouble(BounceAction):
    def __init__(self, unit: Memosprite) -> None:
        super().__init__("Baddies! Trouble!", unit, ActionFlag.attack | ActionFlag.bounce | ActionFlag.aoe)
        self.bounce_scale = data.mem_attack_dmg_scale[unit.master.memosprite_skill_level - 1][0]
        self.aoe_scale = data.mem_attack_dmg_scale[unit.master.memosprite_skill_level - 1][1]

    @property
    def mem(self):
        mem = self.unit
        assert isinstance(mem, Mem)
        return mem

    def run(self):
        for _ in range(4):
            target = self.bounce()
            deal_damage(self, self.unit, target, self.bounce_scale, 5, DamageFlag(), ElementFlag.ice)
            regenerate_energy(self, self.mem.master, 2, True)
        for target in self.unit.select_enemies():
            self.add_target(target)
            deal_damage(self, self.unit, target, self.aoe_scale, 10, DamageFlag(), ElementFlag.ice)
            regenerate_energy(self, self.mem.master, 2, True)
        if self.mem.master.check_trace(2):
            self.mem.regenerate_energy(data.t2_energy)


class FriendsTogether(Buff):
    def __init__(self, source: Mem, unit: Unit) -> None:
        super().__init__(source, "Friends! Together!", unit, 0, TickType.none, False)
        self.converted_cd = data.mem_talent_crit_dmg[source.master.memosprite_talent_level - 1][0]
        self.fixed_cd = data.mem_talent_crit_dmg[source.master.memosprite_talent_level - 1][1]
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
        else:
            super().__init__(source, "Mem's Support", unit, 3, TickType.start_end)
            mem = self.get_source(Mem)
            assert mem is not None
            self.base_scale = data.mem_support_scale[mem.master.memosprite_skill_level - 1]
            self.trace3_enabled = mem.master.check_trace(3)
            self.eidolon1_enabled = mem.master.check_eidolon(1)
            self.eidolon4_enabled = mem.master.check_eidolon(4)
            self.is_copy = False
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
        self.listener = listen(EventDamage, self.on_damage, Priority.Event.true_damage)
        self.listener2 = listen(EventEnterBattle, self.on_enter_battle)
        self.stats = Stats(CRIT_Rate(data.e1_dmg_crit)) if self.eidolon1_enabled else Stats()
        self.unit.stats += self.stats
        if self.is_copy:
            assert isinstance(self.source, MemsSupport)
            self.source.copy_buffs.append(self)
        elif self.eidolon1_enabled:
            if isinstance(self.unit, RemembranceCharacter):
                for tracer in self.unit.get_mods(MemospriteTracer):
                    MemsSupport(self, tracer.sprite).add()
            elif isinstance(self.unit, Memosprite):
                MemsSupport(self, self.unit.master).add()
        return super().add()

    def remove(self):
        self.listener.remove()
        self.listener2.remove()
        self.unit.stats -= self.stats
        for copy in self.copy_buffs:
            if copy._keep_ref is None:  # already removed
                continue
            copy.remove()
        return super().remove()

    def on_damage(self, event: EventDamage):
        if event.damage.unit is not self.unit:
            return
        if isinstance(event.damage, TrueDamage):
            return
        TrueDamage(self, self.unit, event.damage.target, event.damage.calc() * self.scale).deal()

    def on_enter_battle(self, event: EventEnterBattle):
        if not self.eidolon1_enabled:
            return
        if self.is_copy:
            return
        if not isinstance(event.unit, Memosprite):
            return
        if event.unit.master is not self.unit:
            return
        MemsSupport(self, event.unit).add()


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
            self.main_target.action_advance(self.main_target.runner_data.distance)
        MemsSupport(self, self.main_target).add()


class RMC(RemembranceCharacter):
    def __init__(
        self,
        team: Team,
        stats: Stats | None = None,
        basic_level=6,
        skill_level=10,
        ult_level=10,
        talent_level=10,
        memosprite_skill_level=6,
        memosprite_talent_level=6,
        eidolon_level=6,
        trace_level=3,
    ) -> None:
        if stats is None:
            stats = data.base_stats.deepcopy()
        super().__init__("Trailblazer", "RMC", stats, team, basic_level, skill_level, ult_level, talent_level, memosprite_skill_level, memosprite_talent_level, eidolon_level, trace_level)
        self.mem_summoned = False
        self.e2_enabled = True
        RMCAP(self, self, False).add()
        UltActivator(self, RMCUltProvider(self, self, False)).add()

    def add(self, index=-1):
        self.listener = listen(EventTurn, self.on_turn)
        self.listener2 = listen(EventAction, self.on_action)
        self.listener3 = listen(EventDamage, self.on_damage)
        super().add(index)
        if self.check_trace(1):
            self.action_advance(data.t1_action_advance)
        if self.check_eidolon(3):
            self.skill_level += 2
            self.talent_level += 2
            self.memosprite_talent_level += 1
        if self.check_eidolon(5):
            self.ult_level += 2
            self.basic_level += 1
            self.memosprite_skill_level += 1

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
        mem_tracer.sprite.regenerate_energy(data.e4_mem_energy)

    def on_damage(self, event: EventDamage):
        if not self.check_eidolon(6):
            return
        if not isinstance(event.damage.source, Ult):
            return
        if not isinstance(event.damage.unit, Mem):
            return
        if event.damage.unit.master is not self:
            return
        event.damage.source_stats.locks.append(CRIT_Rate(data.e6_crit_rate))

    def generate_memosprite_stats(self):
        stats = data.mem_base_stats.deepcopy()
        hp_stat = self.stats.get_stat(HP, exclusive_flag=ConvertFlag.convert)
        base_hp = data.talent_hp[self.talent_level - 1][0] * hp_stat.get_base()
        flat_hp = data.talent_hp[self.talent_level - 1][1] + hp_stat.get_value() - hp_stat.get_base()
        stats.stats.append(HP(base=base_hp, flat=flat_hp))
        return stats


class Basic(Action):
    def __init__(self, unit: Character, target: Unit) -> None:
        super().__init__("Leave It to Me!", unit, ActionFlag.attack | ActionFlag.basic | ActionFlag.single)
        self.main_target = target
        self.scale = data.basic_dmg_scale[unit.basic_level - 1]

    def run(self):
        assert self.main_target is not None
        self.unit.team.gain_skill_point(self, 1)
        self.add_target(self.main_target)
        deal_damage(self, self.unit, self.main_target, self.scale, 10, DamageFlag.basic, ElementFlag.ice)
        regenerate_energy(self, self.unit, 20, True)


class Skill(Action):
    def __init__(self, unit: Character) -> None:
        super().__init__("I Choose You!", unit, ActionFlag.skill | ActionFlag.single)
        self.main_target = unit
        self.heal_percent = data.skill_heal[unit.skill_level - 1]
        self.energy_regenerate = data.skill_energy

    def run(self):
        assert isinstance(self.unit, RMC)
        self.unit.team.cost_skill_point(self, 1)
        self.add_target(self.unit)
        if mem_tracer := self.unit.get_mod(MemTracer):
            mem = mem_tracer.sprite
            for control in mem.get_mods(Control):
                control.dispel(self)
            Heal(self, self.unit, mem, HealFlag.skill, MaxHPPercentMultipier(self.heal_percent)).deal()
            mem.regenerate_energy(self.energy_regenerate)
        else:
            mem = Mem(self.unit.generate_memosprite_stats(), self.unit)
            mem.add()
        regenerate_energy(self, self.unit, 30, True)


class Ult(Action):
    def __init__(self, unit: Character) -> None:
        super().__init__("Together, Mem!", unit, ActionFlag.aoe | ActionFlag.attack | ActionFlag.ult)
        self.scale = data.ult_dmg_scale[unit.ult_level - 1]
        self.energy_regenerate = data.ult_energy

    def run(self):
        assert isinstance(self.unit, RMC)
        self.unit.status[Energy, self] -= 160
        if mem_tracer := self.unit.get_mod(MemTracer):
            mem = mem_tracer.sprite
            for control in mem.get_mods(Control):
                control.dispel(self)
        else:
            mem = Mem(self.unit.generate_memosprite_stats(), self.unit)
            mem.add()
        mem.regenerate_energy(self.energy_regenerate)
        for enemy in mem.select_enemies():
            self.add_target(enemy)
            deal_damage(self, mem, enemy, self.scale, 20, DamageFlag.ult, ElementFlag.ice)
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


class ForceAttack(ActionSelector):
    def __init__(self, unit: Unit) -> None:
        super().__init__(ForceAttackController(), unit, -1)


class ForceAttackController(Controller):
    def choose_action(self, actions: list[Action], allow_skip=False) -> Action | None:
        if len(actions) > 0:
            return actions[0]
        return None
