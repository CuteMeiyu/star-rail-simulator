import game


class Relic(game.Mod):
    def __init__(self, name: str, unit: game.Unit, stats: game.Stats) -> None:
        self.name = name
        self.stats = stats
        super().__init__(unit, unit)

    def add(self):
        self.unit.stats += self.stats
        return super().add()

    def remove(self):
        self.unit.stats -= self.stats
        return super().remove()
