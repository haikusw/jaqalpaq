# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Data type used internally for identifiers."""


class Identifier(tuple):
    """An internal representation of an identifier, possibly qualified by one or more namespaces.

    The default constructor, inherited from tuple, creates a possibly qualified identifier where the highest indexed
    entry is the identifier, and the lowest indexed entry is the outermost namespace.

    To create an identifier from a single string, even one known to not be qualified, use the parse()
    classmethod.

    To return how the original string looked, call str(obj). In other words, str() and .parse() are inverses.

    """

    @classmethod
    def parse(cls, string):
        """Return an identifier formed by parsing the input string."""
        return Identifier(string.split("."))

    def __repr__(self):
        return f"Identifier({'.'.join(str(v) for v in self)})"

    def __str__(self):
        return ".".join(str(v) for v in self)
