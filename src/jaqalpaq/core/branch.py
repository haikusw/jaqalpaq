# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from .block import BlockStatement
from ..error import JaqalError

# Set this to True before parsing anything with branches
USE_EXPERIMENTAL_BRANCH = False


class BranchStatement:
    """
    Represents a Jaqal branch statement containing case statements.

    :param statements: The different branch cases; defaults to an empty list.
    :type statements: list[CaseStatement]
    """

    def __init__(self, cases=None):
        if not USE_EXPERIMENTAL_BRANCH:
            raise JaqalError(
                "Branches are an experimental feature not yet officially supported. Set USE_EXPERIMENTAL_BRANCH to True to use them anyway."
            )
        if cases is None:
            self._cases = []
        else:
            self._cases = cases

    def __repr__(self):
        return f"BranchStatement({self.cases})"

    def __eq__(self, other):
        try:
            return self.cases == other.cases
        except AttributeError:
            return False

    @property
    def cases(self):
        """
        The contents of the block. In addition to read-only access through this property,
        a basic sequence protocol (``len()``, iteration, and indexing) is also
        supported to access the contents.
        """
        return self._cases

    def __getitem__(self, key):
        return self.cases[key]

    def __iter__(self):
        return iter(self.cases)

    def __len__(self):
        return len(self.cases)


class CaseStatement:
    """
    Represents a Jaqal case statement.

    :param str state: The case for which to apply the associated block statement.
    :param BlockStatement statements: The block to apply for the specified state.
    """

    def __init__(self, state, statements=None):
        self._state = state
        if statements is None:
            self._statements = BlockStatement()
        else:
            self._statements = statements

    def __repr__(self):
        return f"CaseStatement({self.state:04b}, {self.statements})"

    def __eq__(self, other):
        try:
            return self.state == other.state and self.statements == other.statements
        except AttributeError:
            return False

    @property
    def state(self):
        """The binary representation of a measurements state. If the state
        matches a measurement outcome, statements will be run"""
        return self._state

    @property
    def statements(self):
        """
        The block of statements in this branch. In addition to read-only access
        through this property, the same basic sequence protocol (``len()``, iteration,
        and indexing) that the :class:`BlockStatement` supports can also be used and will be passed through.
        """
        return self._statements

    def __getitem__(self, key):
        return self.statements[key]

    def __iter__(self):
        return iter(self.statements)

    def __len__(self):
        return len(self.statements)
