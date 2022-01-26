# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.

from jaqalpaq.error import JaqalError


class BlockStatement:
    """
    Represents a Jaqal block statement; either sequential or parallel. Can contain other
    blocks, loop statements, and gate statements.

    :param bool parallel: Set to False (default) for a sequential block or True for a
        parallel block.
    :param bool subcircuit: Set to False (default) for a standard sequential or parallel
        block of statements. Set to True to include an implicit prepare and measure as
        the first and last statements of this block.
    :param bool iterations: The number of times a subcircuit block is run on the
        hardware. Not used for non-subcircuit blocks.
    :param statements: The contents of the block; defaults to an empty block.
    :type statements: list(GateStatement, LoopStatement, BlockStatement)
    """

    def __init__(self, parallel=False, subcircuit=False, iterations=1, statements=None):
        self._parallel = bool(parallel)
        self._subcircuit = bool(subcircuit)
        self._iterations = iterations
        if not self._subcircuit and self._iterations != 1:
            raise JaqalError("Only subcircuits may have iterations != 1")
        if statements is None:
            self._statements = []
        else:
            self._statements = statements

    def __repr__(self):
        return f"BlockStatement(parallel={self.parallel}, subcircuit={self.subcircuit}, iterations={self.iterations}, {self.statements})"

    def __eq__(self, other):
        try:
            return (
                self.parallel == other.parallel
                and self.subcircuit == other.subcircuit
                and self.iterations == other.iterations
                and self.statements == other.statements
            )
        except AttributeError:
            return False

    @property
    def parallel(self):
        """True if this is a parallel block, False if sequential."""
        return self._parallel

    @property
    def subcircuit(self):
        """True if this is a subcircuit block, False otherwise."""
        return self._subcircuit

    @property
    def iterations(self):
        """The number of times this block is run on the hardware. Only valid
        for subcircuit blocks; it will always return 1 otherwise."""
        return self._iterations

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
