from numpy.random import choice
from numpy import array
from collections import OrderedDict

from jaqalpaq import JaqalError
from jaqalpaq.parser import parse_jaqal_file, parse_jaqal_string
from jaqalpaq.core.result import (
    ExecutionResult,
    ProbabilisticPTMCircuit,
    MeasurementResult,
)
from jaqalpaq.core.algorithm.visitor import Visitor
from jaqalpaq.core.algorithm.walkers import SubcircuitsVisitor, DiscoverPTMCircuits
from jaqalpaq.core.algorithm import expand_macros, fill_in_let
from .pygsti.frontend import ptmcircuit_probabilities


class EmulatorWalker(SubcircuitsVisitor):
    def __init__(self, subcircuits, probabilities):
        """(internal) Instantiates an EmulationWalker.

        Produce emulated output sampled from a given probability distribution.

        :param List[Subcircuit] subcircuits: the prepare_all/measure_all subcircuits
        :param List[List[Float]] probabilities: the probabilities of each outcome

        """
        super().__init__(subcircuits)
        self.ptm_circuits = []
        self.res = []
        self.meas_index = 0
        for n, (sc, prob) in enumerate(zip(self.subcircuits, probabilities)):
            self.ptm_circuits.append(ProbabilisticPTMCircuit(sc, n, [], prob))
        # This is only valid because we must alway do measure_all.
        if self.subcircuits:
            self.qubits = len(self.subcircuits[0].used_qubits)

    def process_subcircuit(self):
        ptm_circuit = self.ptm_circuits[self.index]
        nxt = choice(2 ** self.qubits, p=ptm_circuit.probabilities)
        mr = MeasurementResult(nxt, self.meas_index, ptm_circuit)
        self.res.append(mr)
        ptm_circuit._measurements.append(mr)
        self.meas_index += 1


def generate_probabilities(circ, subcircuits):
    """(internal) Attaches noiseless result probablities to an execution result object.

    :param ExecutionResult exe_res: The execution result object to process.
    :param prob_kwargs: Optional (undocumented) arguments to pass to
        :meth:`subexperiment_probabilities`.
    :type prob_kwargs: dict or None

    The sub-experiments of exe_res learn their noiseless result probabilities.

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    probabilities = []
    for sc in subcircuits:
        p = ptmcircuit_probabilities(circ, sc)
        probs = array([(int(k[0][::-1], 2), v) for k, v in p.items()])
        probabilities.append(probs[probs[:, 0].argsort()][:, 1].copy())

    return probabilities


def run_jaqal_circuit(circuit):
    """Execute a Jaqal :class:`Circuit` in a noiseless emulator.

    :param Circuit circuit: The Jaqalpaq circuit to be run.

    :returns: An :class:`ExecutionResult` object.

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    circuit = expand_macros(fill_in_let(circuit))
    visitor = DiscoverPTMCircuits()
    subcircuits = visitor.visit(circuit)
    w = EmulatorWalker(subcircuits, generate_probabilities(circuit, subcircuits))
    w.visit(circuit)
    return ExecutionResult(w.ptm_circuits, w.res)


def run_jaqal_string(jaqal):
    """Execute a Jaqal string in a noiseless emulator.

    :param str jaqal: The literal Jaqal program text.

    :returns: An :class:`ExecutionResult` object.

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    return run_jaqal_circuit(parse_jaqal_string(jaqal, autoload_pulses=True))


def run_jaqal_file(fname):
    """Execute a Jaqal program in a file in a noiseless emulator.

    :param str fname: The path to a Jaqal file to execute.

    :returns: An :class:`ExecutionResult` object.

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    return run_jaqal_circuit(parse_jaqal_file(fname, autoload_pulses=True))


__all__ = [
    "run_jaqal_string",
    "run_jaqal_file",
    "run_jaqal_circuit",
]
