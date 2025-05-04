import game


class Lightcone(game.SourcelessMod):
    def __init__(self, unit: game.Unit, stats: game.Stats) -> None:
        super().__init__(unit)
        self.stats = stats

    def add(self):
        self.unit.stats += self.stats
        return super().add()

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()
