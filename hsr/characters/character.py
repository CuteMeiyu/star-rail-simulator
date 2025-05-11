import abc

import game


class Character(game.Unit, abc.ABC):
    def __init__(
        self,
        name: str,
        schedule_name: str,
        team: game.Team,
        ascension=6,
        level=80,
        basic_level=6,
        skill_level=10,
        ult_level=10,
        talent_level=10,
        eidolon_level=0,
        trace_flags: tuple[bool, ...] = (),
        trace_stats_flags: tuple[bool, ...] = (),
    ) -> None:
        super().__init__(name, schedule_name, self.generate_base_stats(ascension, level), team)
        self.basic_level = basic_level
        self.skill_level = skill_level
        self.ult_level = ult_level
        self.talent_level = talent_level
        self.eidolon_flag: list[bool] = []
        self.trace_flag: list[bool] = []
        self.set_eidolon_level(eidolon_level)
        self.set_trace(*trace_flags)
        self.stats.add(self.get_trace_stats(*trace_stats_flags))

    @abc.abstractmethod
    def generate_base_stats(self, ascension: int, level: int) -> game.Stats: ...

    @abc.abstractmethod
    def get_trace_stats(self, *trace_stats_flags: bool) -> game.Stats: ...

    def set_trace(self, t1: bool, t2: bool, t3: bool):
        self.trace_flag = [t1, t2, t3]

    def set_trace_level(self, trace_level: int):
        if trace_level > 3:
            trace_level = 3
        self.set_trace(trace_level >= 1, trace_level >= 2, trace_level >= 3)

    def check_trace(self, trace_level: int):
        return self.trace_flag[trace_level - 1]

    def set_eidolon(self, e1: bool, e2: bool, e3: bool, e4: bool, e5: bool, e6: bool):
        self.eidolon_flag = [e1, e2, e3, e4, e5, e6]

    def set_eidolon_level(self, eidolon_level: int):
        if eidolon_level > 6:
            eidolon_level = 6
        self.set_eidolon(
            eidolon_level >= 1,
            eidolon_level >= 2,
            eidolon_level >= 3,
            eidolon_level >= 4,
            eidolon_level >= 5,
            eidolon_level >= 6,
        )

    def check_eidolon(self, eidolon_level: int):
        return self.eidolon_flag[eidolon_level - 1]


class RemembranceCharacter(Character):
    def __init__(
        self,
        name: str,
        schedule_name: str,
        team: game.Team,
        ascension=6,
        level=80,
        basic_level=6,
        skill_level=10,
        ult_level=10,
        talent_level=10,
        memosprite_skill_level=6,
        memosprite_talent_level=6,
        eidolon_level=0,
        trace_flags: tuple[bool, ...] = (True, True, True),
        trace_stats_flags: tuple[bool, ...] = (True,) * 10,
    ) -> None:
        self.memosprite_skill_level = memosprite_skill_level
        self.memosprite_talent_level = memosprite_talent_level
        super().__init__(name, schedule_name, team, ascension, level, basic_level, skill_level, ult_level, talent_level, eidolon_level, trace_flags, trace_stats_flags)


class Memosprite(game.Unit):
    def __init__(self, name: str, schedule_name: str, stats: game.Stats, team: game.Team, master: RemembranceCharacter) -> None:
        super().__init__(name, schedule_name, stats, team)
        self.master = master

    def add(self, index=-1):
        self.add_tracer()
        return super().add(index)

    def remove(self):
        self.remove_tracer()
        return super().remove()

    def add_tracer(self):
        MemospriteTracer(self.master, self).add()

    def remove_tracer(self):
        for tracer in self.master.get_mods(MemospriteTracer):
            if tracer.sprite is self:
                tracer.remove()


class MemospriteTracer(game.SourcelessMod):
    def __init__(self, unit: game.Unit, sprite: Memosprite, priority=0) -> None:
        super().__init__(unit, priority)
        self.sprite = sprite
