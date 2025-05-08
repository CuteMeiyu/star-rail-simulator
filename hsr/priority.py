current_negative = -0xFFFF
current_positive = 0


def auto_negative():
    global current_negative
    current_negative += 1
    return current_negative


def auto_positive():
    global current_positive
    current_positive += 1
    return current_positive


class Priority:
    class Node:
        # Negative
        death = auto_negative()
        action_end = auto_negative()
        ult_activate = auto_negative()
        counter = auto_negative()
        follow_up = auto_negative()

        # Positive
        turn = auto_positive()

    class Event:
        # ActionEnd
        over_turn = auto_negative()

        # StatusChange
        status_cap = auto_negative()

        # WeaknessBreak
        break_debuff = auto_negative()

        # Death
        killing_energy = auto_negative()

        # Turn
        frozen_dot = auto_positive()
        entanglement_dot = auto_positive()
        dot = auto_positive()
        unfreeze = auto_positive()
        buff_tick = auto_positive()
        weakness_restore = auto_positive()

        # Damage
        true_damage = auto_positive()
        damage_print = auto_positive()

    @staticmethod
    def auto_positive():
        return auto_positive()

    @staticmethod
    def auto_negative():
        return auto_negative()
