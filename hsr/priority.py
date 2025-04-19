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

        # Positive
        turn = auto_positive()

    class Event:
        # Negative
        first = auto_negative()
        status_cap = auto_negative()

        # Positive
        last = auto_positive()

    @staticmethod
    def auto_positive():
        return auto_positive()

    @staticmethod
    def auto_negative():
        return auto_negative()
