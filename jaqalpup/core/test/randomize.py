import random


def make_char_range(start_char, end_char):
    return [chr(v) for v in range(ord(start_char), ord(end_char) + 1)]


start_chars = make_char_range('a', 'z') + make_char_range('A', 'Z') + ['_']
continue_chars = start_chars + make_char_range('0', '9')


def random_identifier(count=None, rand=None):
    """Return a random identifier of the given length."""
    rand = resolve_random_instance(rand)
    if count is None:
        count = random_whole(rand=rand)
    else:
        if not isinstance(count, int):
            raise TypeError("Count must be an integer")
        if count < 1:
            raise ValueError("Count must be at least 1")
    first_chars = rand.choices(start_chars, k=1)
    if count == 1:
        rest_chars = []
    else:
        assert count > 1, f"Bad count: {count}"
        rest_chars = rand.choices(continue_chars, k=count - 1)
    return ''.join(first_chars + rest_chars)


def random_whole(*, lower=1, upper=100, rand=None):
    """Return a random whole number (nonzero integer)."""
    if lower < 1:
        raise ValueError(f"Numbers < 1 are not whole numbers")
    rand = resolve_random_instance(rand)
    return rand.randint(lower, upper)


def random_integer(*, lower=-100, upper=100, rand=None):
    """Return a random integer."""
    rand = resolve_random_instance(rand)
    return rand.randint(lower, upper)


def resolve_random_instance(rand):
    """Return the input argument or the global random instance if the input
    argument is None"""
    if rand is None:
        rand = random._inst
    return rand
