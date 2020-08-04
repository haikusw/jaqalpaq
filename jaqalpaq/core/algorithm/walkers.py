# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from collections import defaultdict
from itertools import chain

from .used_qubit_visitor import UsedQubitIndicesVisitor
from .visitor import Visitor
from jaqalpaq import JaqalError
from jaqalpaq.core.block import BlockStatement, LoopStatement


class Trace:
    """Describes a portion of a Circuit traced out by start and stop locations."""

    def __init__(self, start=None, end=None, used_qubits=None):
        if start is None:
            self.start = []
        else:
            self.start = start

        self.end = end
        self.used_qubits = used_qubits

    def __repr__(self):
        if self.end is None:
            return f"Trace({self.start})"
        else:
            return f"Trace({self.start}, {self.end})"


class TraceSerializer(Visitor):
    """Returns a serialized representation of all gates called during a circuit trace.

    Start locations lexically following stop locations are not supported.

    """

    def __init__(self, trace=None):
        if trace is not None:
            self.start = trace.start
            self.end = trace.end
            self.started = False
        else:
            self.start = None
            self.end = None
            self.started = True

        self.address = []
        self.serialized = []

    def visit_Circuit(self, circuit):
        return self.visit(circuit.body)

    def visit_BlockStatement(self, block):
        address = self.address
        if self.started:
            n = 0
            address.append(n)
        else:
            start = self.start
            if start[: len(address)] != address:
                assert start[: len(address)] > address
                return None
            n = start[len(address)]
            address.append(n)
            if start == address:
                self.started = True

        while n < len(block.statements):
            if self.visit(block.statements[n]):
                return True
            n = address[-1] = n + 1
        address.pop()

        return None

    def visit_LoopStatement(self, loop):
        if self.started:
            for n in range(loop.iterations):
                if self.visit(loop.statements):
                    # We don't support structures like
                    # prepare_all
                    # ...
                    # loop 4 {
                    #  measure_all
                    #  prepare_all
                    #  ...
                    # }
                    raise JaqalError(
                        "measure_all -> prepare_all not supported in loops"
                    )
        else:
            return self.visit(loop.statements)

    def visit_GateStatement(self, gate):
        # We could instead do this with async to use constant additional space.
        self.serialized.append(gate)
        if self.end and (self.address == self.end):
            return True

        return None


class DiscoverSubcircuits(UsedQubitIndicesVisitor):
    """Walks a Circuit, identifying subcircuits bounded by prepare_all and measure_all"""

    # While this *is* the behavior of DiscoverSubcircuits, this flag does nothing.
    validate_parallel = True

    def __init__(self, *args, p_gate="prepare_all", m_gate="measure_all", **kwargs):
        super().__init__(*args, **kwargs)
        self.current = None
        self.subcircuits = []
        self.address = []
        self.p_gate = p_gate
        self.m_gate = m_gate

    def visit_Circuit(self, circuit, context=None):
        # All qubits will be used in every subcircuit, because it is bounded by
        # prepare_all and measure_all.  In the future, we presumably will employ the used
        # qubit functionality of the superclass, and separately report the measured
        # qubits.  But we do not support partial measurements yet.
        self.qubits = list(chain.from_iterable(circuit.fundamental_registers()))
        super().visit_Circuit(circuit, context=context)

        subcircuits = self.subcircuits
        if len(subcircuits) == 0:
            return ()

        if subcircuits[-1].end is None:
            return subcircuits[:-1]
        else:
            return subcircuits[:]

    def visit_BlockStatement(self, block, context=None):
        # Calling UsedQubitIndicesVisitor as super() is
        # far too inflexible for the purposes here.
        indices = defaultdict(set)

        self.address.append(0)
        for self.address[-1], stmt in enumerate(block.statements):
            self.merge_into(
                indices, self.visit(stmt, context=context), disjoint=block.parallel
            )
        self.address.pop()

        return indices

    def visit_GateStatement(self, gate, context=None):
        if gate.name == self.p_gate:
            # We allow for multiple prepare_all's in a row. But gates between those
            # prepare_all's do nothing. Notice also, we would not yet know what the
            # measured or used qubits are, if we had partial measurements.  That would
            # have to wait until the measurement.
            c = self.current = Trace(self.address[:])
        elif gate.name == self.m_gate:
            if self.current is None:
                raise JaqalError(f"{self.p_gate} must follow a {self.m_gate}")
            self.current.end = self.address[:]
            self.current.used_qubits = self.qubits
            self.subcircuits.append(self.current)
            self.current = None
        else:
            if self.current is None:
                raise JaqalError(f"gates must follow a {self.p_gate}")

        return super().visit_GateStatement(gate, context=context)


class TraceVisitor(Visitor):
    """Call process_trace at the start of every trace in execution order."""

    def __init__(self, traces):
        self.traces = traces
        self.address = []
        self.index = 0

    def process_trace(self):
        raise NotImplementedError()

    def visit_Circuit(self, circuit):
        if len(self.traces) == 0:
            return
        self.objective = self.traces[self.index].start

        return self.visit(circuit.body)

    def visit_BlockStatement(self, block):
        first = True
        address = self.address
        while self.objective:
            if address != self.objective[: len(address)]:
                assert not first
                assert address < self.objective[: len(address)]
                return

            first = False

            n = self.objective[len(address)]
            nxt = block.statements[n]
            if (len(address) + 1) == len(self.objective):
                self.process_trace()
                self.index += 1
                if self.index == len(self.traces):
                    # We've found all the traces.  We're done!
                    self.objective = None
                    return
                else:
                    self.objective = self.traces[self.index].start
            else:
                address.append(n)
                self.visit(nxt)
                address.pop()

    def visit_LoopStatement(self, loop):
        # store the walk status
        index = self.index
        address = self.address[:]
        objective = self.objective

        # loop over the classical parts
        for n in range(loop.iterations):
            # Restore the walk status at the start of every loop
            self.objective = objective
            self.address[:] = address[:]
            self.index = index
            self.visit(loop.statements)
