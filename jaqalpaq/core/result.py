from collections import OrderedDict

from .algorithm import fill_in_let, expand_macros
from .algorithm.walkers import *


def parse_jaqal_output_list(circuit, output):
    """Parse experimental output into an ExecutionResult

    :param circuit: the circuit under consideration.
    :type circuit: Circuit
    :param output: the measured qubits, encoded as a string of qubit
        states, or as a little-endian integer (i.e., the state of qubit 0 is in the least
        significant bit; e.g., measuring `100` is encoded as 1, and `001` as 4.)
    :type output: List[int or str]
    :return ExecutionResult: providing collated and uncollated access to the output.
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

        :param output:  The subcircuits bounded at the beginning by a prepare_all
            statement, and at the end by a measure_all statement.
        :type output: List[Subcircuit]
        :param output:  The measurements made during the running of the Jaqal problem.
        :type readouts: List[Readout]

        """
        self._subcircuits = subcircuits
        self._readouts = readouts

    @property
    def readouts(self):
        """An indexable, iterable view of :class:`Readout`s, containing the time-ordered
        measurements and auxiliary data."""
        return self._readouts

    @property
    def subcircuits(self):
        """An indexable, iterable view of the :class:`Subcircuit`s, in lexicographical
        order, containing the readouts due to that subcircuit, as well as additional
        auxiliary data."""
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
        """The measured result encoded as a little-endian integer"""
        return self._result

    @property
    def as_str(self):
        """The measured result encoded as a string of qubit values"""
        return f"{self._result:b}".zfill(len(self.subcircuit.measured_qubits))[::-1]

    def __repr__(self):
        return f"<{type(self).__name__} {self.as_str}>"


class Subcircuit:
    """Encapsulate one part of the circuit between a prepare_all and measure_all gate."""

    def __init__(self, trace, index, readouts):
        """(internal) Instantiate a Subcircuit"""
        self._trace = trace
        self._index = int(index)
        self._readouts = readouts

    @property
    def index(self):
        """The lexical index of this object in the (unrolled) parent circuit."""
        return self._index

    @property
    def readouts(self):
        """An indexable, iterable view of :class:`Readout`s, containing the time-ordered
        measurements and auxiliary data, restricted to this Subcircuit."""
        return self._readouts

    @property
    def measured_qubits(self):
        """An ist of the qubits that are measured, in their display order."""
        return self._trace.used_qubits

    def __repr__(self):
        return f"<{type(self).__name__}@{self._trace.end}>"


class ProbabilisticSubcircuit(Subcircuit):
    """Encapsulate one part of the circuit between a prepare_all and measure_all gate.

    Also contains a probability distribution."""

    def __init__(self, trace, index, readouts, probabilities):
        """(internal) Instantiate a Subcircuit"""
        super().__init__(trace, index, readouts)
        self._probabilities = probabilities

    @property
    def probabilities(self):
        """Return the probability associated with each measurement result as a
        list, ordered as "000", "001", "010", etc.
        """
        return self._probabilities

    @property
    def probabilities_strdict(self):
        """Return the probability associated with each measurement result
        formatted as a dictionary mapping result strings to their respective
        probabilities."""
        qubits = len(self._trace.used_qubits)
        p = self._probabilities
        return OrderedDict([(f"{n:b}".zfill(qubits)[::-1], v) for n, v in enumerate(p)])


class OutputParser(TraceVisitor):
    """(internal) Walks through execution ouput, sorting into :class:`Subcircuit`s"""

    def __init__(self, traces, output):
        """(internal) Prepares an OutputParser instance.

        :param traces: the prepare_all/measure_all subcircuits
        :type traces: List[Trace]
        :param output: the measurement results
        :type output: List[Str or Int]

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
