import game


class Character(game.Unit):
    def __init__(
        self,
        name: str,
        schedule_name: str,
        stats: game.Stats,
        team: game.Team,
        basic_level=6,
        skill_level=10,
        ult_level=10,
        talent_level=10,
        eidolon_level=0,
        trace_level=3,
    ) -> None:
        super().__init__(name, schedule_name, stats, team)
        self.basic_level = basic_level
        self.skill_level = skill_level
        self.ult_level = ult_level
        self.talent_level = talent_level
        self.trace_flag = 0
        self.set_trace_level(trace_level)
        self.eidolon_flag = 0
        self.set_eidolon_level(eidolon_level)

    def set_trace(self, t1: bool, t2: bool, t3: bool):
        self.trace_flag = (t1 << 2) | (t2 << 1) | (t3 << 0)

    def set_trace_level(self, trace_level: int):
        if trace_level > 3:
            trace_level = 3
        self.set_trace(trace_level >= 1, trace_level >= 2, trace_level >= 3)

    def check_trace(self, trace_level: int):
        return self.trace_flag & (0b1000 >> trace_level) > 0

    def enable_trace(self, trace_level: int):
        self.trace_flag |= 0b1000 >> trace_level

    def disable_trace(self, trace_level: int):
        self.trace_flag &= ~(0b1000 >> trace_level)

    def set_eidolon(self, e1: bool, e2: bool, e3: bool, e4: bool, e5: bool, e6: bool):
        self.eidolon_flag = (e1 << 5) | (e2 << 4) | (e3 << 3) | (e4 << 2) | (e5 << 1) | (e6 << 0)

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
        return self.eidolon_flag & (0b1000000 >> eidolon_level) > 0

    def enable_eidolon(self, eidolon_level: int):
        self.eidolon_flag |= 0b1000000 >> eidolon_level

    def disable_eidolon(self, eidolon_level: int):
        self.eidolon_flag &= ~(0b1000000 >> eidolon_level)


class Enemy(game.Unit):
    def __init__(self, name: str, schedule_name: str, stats: game.Stats, team: game.Team) -> None:
        super().__init__(name, schedule_name, stats, team)
        self.status[game.stats.Toughness] = self.stats[game.stats.Toughness]
