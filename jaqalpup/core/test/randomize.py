import random
import sys


def make_char_range(start_char, end_char):
    return [chr(v) for v in range(ord(start_char), ord(end_char) + 1)]


start_chars = make_char_range('a', 'z') + make_char_range('A', 'Z') + ['_']
continue_chars = start_chars + make_char_range('0', '9')


def random_identifier(count=None):
    """Return a random identifier of the given length."""
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
    return ''.join(first_chars + rest_chars)


def random_whole(*, lower=1, upper=100):
    """Return a random whole number (nonzero integer)."""
    if lower < 1:
        raise ValueError(f"Numbers < 1 are not whole numbers")
    return random.randint(lower, upper)


def random_integer(*, lower=-100, upper=100):
    """Return a random integer."""
    return random.randint(lower, upper)


def random_float(*, lower=-sys.float_info.max, upper=sys.float_info.max, rand=None):
    """Return a random floating point number."""
    return rand.uniform(lower, upper)
