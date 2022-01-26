import random
import sys

from jaqalpaq.utilities import RESERVED_WORDS


def make_char_range(start_char, end_char):
    return [chr(v) for v in range(ord(start_char), ord(end_char) + 1)]


start_chars = make_char_range("a", "z") + make_char_range("A", "Z") + ["_"]
continue_chars = start_chars + make_char_range("0", "9")


def random_identifier(count=None):
    """Return a random identifier of the given length."""
    while True:
        if count is None:
            count = random_whole()
        else:
            if not isinstance(count, int):
                raise TypeError("Count must be an integer")
            if count < 1:
                raise ValueError("Count must be at least 1")
        first_chars = random.choices(start_chars, k=1)
        if count == 1:
            rest_chars = []
        else:
            assert count > 1, f"Bad count: {count}"
            rest_chars = random.choices(continue_chars, k=count - 1)
        ident = "".join(first_chars + rest_chars)
        if ident not in RESERVED_WORDS:
            return ident


def random_whole(*, lower=1, upper=100):
    """Return a random whole number (nonzero integer)."""
    if lower < 1:
        raise ValueError(f"Numbers < 1 are not whole numbers")
    return random.randint(lower, upper)


def random_integer(*, lower=-100, upper=100):
    """Return a random integer."""
    return random.randint(lower, upper)


def random_float():
    """Return a random floating point number. Will sometimes return inf or nan."""
    if random.uniform(0, 1) < 0.1:
        return float("inf")
    elif random.uniform(0, 1) < 0.1:
        return float("nan")
    while True:
        mantissa = random.uniform(0, 1)
        exponent = random.randint(sys.float_info.min_10_exp, sys.float_info.max_10_exp)
        sign = random.choice([-1, 1])
        try:
            value = sign * mantissa * 10**exponent
        except OverflowError:
            print(f"Could not create float {sign}*{mantissa}**{exponent}")
            raise
        if value != int(value):
            # The odds of this not being true are astoundingly low, but in case some
            # tests rely on this, best to be sure.
            return value
