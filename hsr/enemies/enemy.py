import game


class Enemy(game.Unit):
    def __init__(self, name: str, schedule_name: str, stats: game.Stats, team: game.Team, elite: bool) -> None:
        super().__init__(name, schedule_name, stats, team)
        self.status[game.stats.Toughness] = self.stats[game.stats.Toughness]
        self.elite = elite
