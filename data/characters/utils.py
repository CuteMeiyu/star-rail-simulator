from hsrgame.stats import CRIT_DMG, CRIT_Rate, Level, Stats


def generate_lv10_data(start: float, step: float):
    return [i * step + start for i in range(10)]


def generate_lv15_data(start: float, step1: float, step2: float):
    seq1 = [i * step1 + start for i in range(6)]
    seq2 = [(i + 1) * step2 + seq1[-1] for i in range(4)]
    seq3 = [(i + 1) * step1 + seq2[-1] for i in range(5)]
    return seq1 + seq2 + seq3
