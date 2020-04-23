import re

from jaqal import RESERVED_WORDS

valid_identifier_regex = re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')


def is_identifier_valid(name):
    """Return whether an identifier is syntactically valid.

    :param str name: The name of the identifier.
    :return: Whether the type is valid.
    :rtype: bool
    """
    return valid_identifier_regex.match(name) and name not in RESERVED_WORDS
