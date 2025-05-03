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
        # Negative
        first = auto_negative()
        status_cap = auto_negative()
        weakness_break = auto_negative()
        killing_energy = auto_negative()

        # Positive
        # Turn Event
        frozen_dot = auto_positive()
        entanglement_dot = auto_positive()
        dot = auto_positive()
        unfreeze = auto_positive()
        buff_tick = auto_positive()
        weakness_restore = auto_positive()
        # Damage Event
        true_damage = auto_positive()
        last = auto_positive()

    @staticmethod
    def auto_positive():
        return auto_positive()

    @staticmethod
    def auto_negative():
        return auto_negative()
