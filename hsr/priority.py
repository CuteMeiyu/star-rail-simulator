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
    # Action
    UltActivate = auto_negative()
    Counter = auto_negative()

    # Turn
    Turn = auto_positive()
