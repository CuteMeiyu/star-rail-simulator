from hsrgame.stats import *

from ...utils import generate_lv10_data, generate_lv15_data

base_stats = Stats(
    HP(base=1023.1),
    ATK(base=652.68),
    DEF(base=441.0),
    SPD(base=98.0),
    Energy(base=140.0),
    Aggro(base=75.0),
    Level(80),
    CRIT_Rate(0.05),
    CRIT_DMG(0.5),
    Path(Paths.erudition),
    CombatType(CombatTypes.quantum),
)

basic_scale = generate_lv10_data(0.5, 0.1)
enhaused_basic_main_scale = generate_lv10_data(1.2, 0.14)
enhaused_basic_minor_scale = generate_lv10_data(0.5, 0.1)
skill_dmg_boost = generate_lv15_data(0.14, 0.014, 0.0175)
ult_scale = generate_lv15_data(1.2, 0.08, 0.1)
talent_atk_boost = generate_lv15_data(0.36, 0.036, 0.045)

trace_atk_boost = 0.28
trace_dmg_boost = 0.144
trace_def_boost = 0.125
