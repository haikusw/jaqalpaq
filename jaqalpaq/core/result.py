# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from collections import OrderedDict

from .algorithm import fill_in_let, expand_macros
from .algorithm.walkers import *


def parse_jaqal_output_list(circuit, output):
    """Parse experimental output into an :class:`ExecutionResult` providing collated and
    uncollated access to the output.

    :param Circuit circuit: The circuit under consideration.
    :param output: The measured qubit state, encoded as a string of 1s and 0s, or as an
        int with state of qubit 0 encoded as the least significant bit, and so on.
        For example, Measuring ``100`` is encoded as 1, and ``001`` as 4.
    :type output: list[int or str]
    :returns: The parsed output.
    :rtype: ExecutionResult
    """
    circuit = expand_macros(fill_in_let(circuit))
    visitor = DiscoverSubcircuits()
    w = OutputParser(visitor.visit(circuit), output)
    w.visit(circuit)
    return ExecutionResult(w.subcircuits, w.res)


class ExecutionResult:
    "Captures the results of a Jaqal program's execution, on hardware or an emulator."

    def __init__(self, subcircuits, readouts):
        """(internal) Initializes an ExecutionResult object.

        :param list[Subcircuit] output:  The subcircuits bounded at the beginning by a
            prepare_all statement, and at the end by a measure_all statement.
        :param list[Readout] output:  The measurements made during the running of the
            Jaqal problem.

        """
        self._subcircuits = subcircuits
        self._readouts = readouts

    @property
    def readouts(self):
        """An indexable, iterable view of :class:`Readout` objects, containing the
        time-ordered measurements and auxiliary data."""
        return self._readouts

    @property
    def subcircuits(self):
        """An indexable, iterable view of the :class:`Subcircuit` objects, in
        :term:`flat order`, containing the readouts due to that subcircuit, as well as
        additional auxiliary data."""
        return self._subcircuits


class Readout:
    """Encapsulate the result of measurement of some number of qubits."""

    def __init__(self, result, index, subcircuit):
        """(internal) Instantiate a Readout object

        Contains the actual results of a measurement.
        """
        self._result = result
        self._index = index
        self._subcircuit = subcircuit

    @property
    def index(self):
        """The temporal index of this measurement in the parent circuit."""
        return self._index

    @property
    def subcircuit(self):
        """Return the associated prepare_all/measure_all block in the parent circuit."""
        return self._subcircuit

    @property
    def as_int(self):
        """The measured result encoded as an integer, with qubit 0 represented by the
        least significant bit."""
        return self._result

    @property
    def as_str(self):
        """The measured result encoded as a string of qubit values."""
        return f"{self._result:b}".zfill(len(self.subcircuit.measured_qubits))[::-1]

    def __repr__(self):
        return f"<{type(self).__name__} {self.as_str} index {self._index} from {self._subcircuit.index}>"


class Subcircuit:
    """Encapsulate one part of the circuit between a prepare_all and measure_all gate."""

    def __init__(self, trace, index, readouts):
        """(internal) Instantiate a Subcircuit"""
        self._trace = trace
        self._index = int(index)
        self._readouts = readouts

    @property
    def index(self):
        """The :term:`flat order` index of this object in the (unrolled) parent circuit."""
        return self._index

    @property
    def readouts(self):
        """An indexable, iterable view of :class:`Readout` objects, containing the
        time-ordered measurements and auxiliary data, restricted to this Subcircuit."""
        return self._readouts

    @property
    def measured_qubits(self):
        """An ist of the qubits that are measured, in their display order."""
        return self._trace.used_qubits

    def __repr__(self):
        return f"<{type(self).__name__} {self._index}@{self._trace.end}>"


class ProbabilisticSubcircuit(Subcircuit):
    """Encapsulate one part of the circuit between a prepare_all and measure_all gate.

    Also contains a probability distribution."""

    def __init__(self, trace, index, readouts, probabilities):
        """(internal) Instantiate a Subcircuit"""
        super().__init__(trace, index, readouts)
        self._probabilities = probabilities

    @property
    def probability_by_int(self):
        """Return the probability associated with each measurement result as a list,
        ordered by the integer representation of the result, with least significant bit
        representing qubit 0.  I.e., "000" for 0b000, "100" for 0b001, "010" for 0b010,
        etc.
        """
        return self._probabilities

    @property
    def probability_by_str(self):
        """Return the probability associated with each measurement result formatted as a
        dictionary mapping result strings to their respective probabilities."""
        qubits = len(self._trace.used_qubits)
        p = self._probabilities
        return OrderedDict([(f"{n:b}".zfill(qubits)[::-1], v) for n, v in enumerate(p)])


class OutputParser(TraceVisitor):
    """(internal) Walks through execution ouput, sorting into :class:`Subcircuit`s"""

    def __init__(self, traces, output):
        """(internal) Prepares an OutputParser instance.

        :param list[Trace] traces: the prepare_all/measure_all subcircuits
        :param output: the measurement results
        :type output: list[Str or Int]

        """
        super().__init__(traces)
        self.data = iter(output)
        self.subcircuits = []
        self.res = []
        self.readout_index = 0
        for n, sc in enumerate(self.traces):
            self.subcircuits.append(Subcircuit(sc, n, []))

    def process_trace(self):
        subcircuit = self.subcircuits[self.index]
        nxt = next(self.data)
        if isinstance(nxt, str):
            nxt = int(nxt[::-1], 2)
        mr = Readout(nxt, self.readout_index, subcircuit)
        self.res.append(mr)
        subcircuit._readouts.append(mr)
        self.readout_index += 1


__all__ = [
    "ExecutionResult",
    "parse_jaqal_output_list",
    "Subcircuit",
    "Readout",
]
