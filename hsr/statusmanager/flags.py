from game import FlexFlag


class DamageFlag(FlexFlag):
    basic: "DamageFlag"
    skill: "DamageFlag"
    ult: "DamageFlag"
    dot: "DamageFlag"
    follow_up: "DamageFlag"
    counter: "DamageFlag"
    additional: "DamageFlag"
    breaking: "DamageFlag"
    super_break: "DamageFlag"


DamageFlag.counter |= DamageFlag.follow_up
DamageFlag.super_break |= DamageFlag.breaking
