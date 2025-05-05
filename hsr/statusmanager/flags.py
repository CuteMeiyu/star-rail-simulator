from game import FlexFlag


class DamageFlag(FlexFlag):
    additional: "DamageFlag"
    breaking: "DamageFlag"
    super_break: "DamageFlag"


DamageFlag.super_break |= DamageFlag.breaking


class HealFlag(FlexFlag):
    placeholder: "HealFlag"
