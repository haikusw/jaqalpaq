# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
class BlockStatement:
    """
    Represents a Jaqal block statement; either sequential or parallel. Can contain other
    blocks, loop statements, and gate statements.

    :param bool parallel: Set to False (default) for a sequential block or True for a parallel block.
    :param statements: The contents of the block; defaults to an empty block.
    :type statements: list(GateStatement, LoopStatement, BlockStatement)
    """

    def __init__(self, parallel=False, statements=None):
        self._parallel = bool(parallel)
        if statements is None:
            self._statements = []
        else:
            self._statements = statements

    def __repr__(self):
        return f"BlockStatement(parallel={self.parallel}, {self.statements})"

    def __eq__(self, other):
        try:
            return (
                self.parallel == other.parallel and self.statements == other.statements
            )
        except AttributeError:
            return False

    @property
    def parallel(self):
        """True if this is a parallel block, False if sequential."""
        return self._parallel

    @property
    def statements(self):
        """
        The contents of the block. In addition to read-only access through this property,
        a basic sequence protocol (``len()``, iteration, and indexing) is also
        supported to access the contents.
        """
        return self._statements

    def __getitem__(self, key):
        return self.statements[key]

    def __iter__(self):
        return iter(self.statements)

    def __len__(self):
        return len(self.statements)


class UnscheduledBlockStatement(BlockStatement):
    """An unscheduled block, which is treated as an ordinary block except by the :mod:`jaqalpaq.scheduler` submodule."""

    pass


class LoopStatement:
    """
    Represents a Jaqal loop statement.

    :param int iterations: The number of times to repeat the loop.
    :param BlockStatement statements: The block to repeat. If omitted, a new sequential block will be created.
    """

    def __init__(self, iterations, statements=None):
        self._iterations = iterations
        if statements is None:
            self._statements = BlockStatement()
        else:
            self._statements = statements

    def __repr__(self):
        return f"LoopStatement({self.iterations}, {self.statements})"

    def __eq__(self, other):
        try:
            return (
                self.iterations == other.iterations
                and self.statements == other.statements
            )
        except AttributeError:
            return False

    @property
    def iterations(self):
        """The number of times this Loop will be executed. May be an integer
        or a let constant or a Macro parameter."""
        return self._iterations

    @property
    def statements(self):
        """
        The block that's repeated by the loop statement. In addition to read-only access
        through this property, the same basic sequence protocol (``len()``, iteration,
        and indexing) that the :class:`BlockStatement` supports can also be used on
        the LoopStatement, and will be passed through.
        """
        return self._statements

    def __getitem__(self, key):
        return self.statements[key]

    def __iter__(self):
        return iter(self.statements)

    def __len__(self):
        return len(self.statements)
