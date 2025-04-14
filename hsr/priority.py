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
        action_end = auto_negative()
        ult_activate = auto_negative()
        death = auto_negative()
        counter = auto_negative()

        # Positive
        turn = auto_positive()

    class Event:
        ## Negative
        first = auto_negative()

        ## Positive
        last = auto_positive()
