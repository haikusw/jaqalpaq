from collections import OrderedDict

from .algorithm import fill_in_let, expand_macros
from .algorithm.walkers import *


def parse_jaqal_output_list(circuit, output):
    """Parse experimental output into an ExecutionResult

    :param Circuit circuit: the circuit under consideration.
    :param List[int or str] output: the measured qubits, encoded as a string of qubit
        states, or as a little-endian integer (i.e., the state of qubit 0 is in the least
        significant bit; e.g., measuring `100` is encoded as 1, and `001` as 4.)
    :return ExecutionResult: providing collated and uncollated access to the output.
    """
    circuit = expand_macros(fill_in_let(circuit))
    visitor = DiscoverPTMCircuits()
    w = OutputParser(visitor.visit(circuit), output)
    w.visit(circuit)
    return ExecutionResult(w.ptm_circuits, w.res)


class ExecutionResult:
    "Captures the results of a Jaqal program's execution, on hardware or an emulator."

    def __init__(self, ptm_circuits, measurements):
        """(internal) Initializes an ExecutionResult object.

        :param List[PTMCircuit] output:  The subcircuits bounded at the beginning by a
            prepare_all statement, and at the end by a measure_all statement.
        :param List[MeasurementResult] output:  The measurements made during the running
            of the Jaqal problem.

        """
        self._ptm_circuits = ptm_circuits
        self._measurements = measurements

    @property
    def measurements(self):
        """An indexable, iterable view of the :class:`MeasurementResult`s, containing the
        collated measurements, and its associated :class:`PTMCircuit`."""
        return self._measurements

    @property
    def ptm_circuits(self):
        """An indexable, iterable view of the :class:`PTMCircuit`s, containing the
        uncollated measurements and probabilities, if applicable."""
        return self._ptm_circuits


class MeasurementResult:
    """Encapsulate the result of measurement of some number of qubits."""

    def __init__(self, result, meas_index, ptm_circuit):
        """(internal) Instantiate a MeasurementResult object

        Contains the actual results of a measurement.
        """
        self._result = result
        self._meas_index = meas_index
        self._ptm_circuit = ptm_circuit

    @property
    def meas_index(self):
        """The temporal index of this measurement in the parent circuit."""
        return self._meas_index

    @property
    def ptm_circuit(self):
        """Return the associated prepare_all/measure_all block in the parent circuit."""
        return self._ptm_circuit

    @property
    def ptm_index(self):
        """The lexicographical index of the prepare_all/measure_all block in the parent
        circuit"""
        return self.ptm_circuit.index

    @property
    def as_int(self):
        """The measured result encoded as a little-endian integer"""
        return self._result

    @property
    def as_str(self):
        """The measured result encoded as a string of qubit values"""
        return f"{self._result:b}".zfill(len(self.ptm_circuit.measured_qubits))[::-1]


class PTMCircuit:
    """Encapsulate one part of the circuit between a prepare_all and measure_all gate."""

    def __init__(self, subcircuit, index, measurements):
        """(internal) Instantiate a PTMCircuit"""
        self._subcircuit = subcircuit
        self._index = int(index)
        self._measurements = measurements

    @property
    def index(self):
        """The index of this object in the parent circuit."""
        return self._index

    @property
    def measurements(self):
        """An indexable, iterable view of the uncollated measurements associated with the
        subcircuit"""
        return self._measurements

    @property
    def measured_qubits(self):
        """An ist of the qubits that are measured, in their display order."""
        return self._subcircuit.used_qubits


class ProbabilisticPTMCircuit(PTMCircuit):
    """Encapsulate one part of the circuit between a prepare_all and measure_all gate.

    Also contains a probability distribution."""

    def __init__(self, subcircuit, index, measurements, probabilities):
        """(internal) Instantiate a PTMCircuit"""
        super().__init__(subcircuit, index, measurements)
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
        qubits = len(self._subcircuit.used_qubits)
        p = self._probabilities
        return OrderedDict([(f"{n:b}".zfill(qubits)[::-1], v) for n, v in enumerate(p)])


class OutputParser(SubcircuitsVisitor):
    """(internal) Walks through execution ouput, sorting into PTMCircuits"""

    def __init__(self, subcircuits, output):
        """(internal) Prepares an OutputParser instance.

        :param List[Subcircuit] subcircuits: the prepare_all/measure_all subcircuits
        :param List[Str or Int] output: the measurement results

        """
        super().__init__(subcircuits)
        self.data = iter(output)
        self.ptm_circuits = []
        self.res = []
        self.meas_index = 0
        for n, sc in enumerate(self.subcircuits):
            self.ptm_circuits.append(PTMCircuit(sc, n, []))

    def process_subcircuit(self):
        ptm_circuit = self.ptm_circuits[self.index]
        nxt = next(self.data)
        if isinstance(nxt, str):
            nxt = int(nxt[::-1], 2)
        mr = MeasurementResult(nxt, self.meas_index, ptm_circuit)
        self.res.append(mr)
        ptm_circuit._measurements.append(mr)
        self.meas_index += 1


__all__ = [
    "ExecutionResult",
    "parse_jaqal_output_list",
    "PTMCircuit",
    "MeasurementResult",
]
