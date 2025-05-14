import game


class Lightcone(game.Mod):
    def __init__(self, name: str, unit: game.Unit, stats: game.Stats) -> None:
        super().__init__(unit, unit)
        self.name = name
        self.stats = stats

    def add(self):
        self.unit.stats += self.stats
        return super().add()

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()
