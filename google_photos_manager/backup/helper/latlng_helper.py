from fractions import Fraction


def to_deg(value, loc):
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg = int(abs_value)
    t1 = (abs_value - deg) * 60
    min = int(t1)
    sec = round((t1 - min) * 60, 5)

    return deg, min, sec, loc_value


def change_to_rational(number):
    f = Fraction(str(number))
    return f.numerator, f.denominator
