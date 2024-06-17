def is_real_number(value: str):
    try:
        float(value)
        return True
    except ValueError:
        return False


def is_positive_real_number(value: str):
    try:
        float(value)
        if float(value) < 0:
            return False
        return True
    except ValueError:
        return False


def is_positive_natural_number(value: str):
    try:
        num = int(value)
        return num > 0
    except ValueError:
        return False
