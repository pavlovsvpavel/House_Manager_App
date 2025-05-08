from math import ceil


def round_up_second_decimal(number):
    shifted_number = number * 100
    rounded_shifted_number = ceil(shifted_number)
    result = rounded_shifted_number / 100

    return result
