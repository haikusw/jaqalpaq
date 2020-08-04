# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from numpy.random import choice
from numpy import array
from collections import OrderedDict

from jaqalpaq import JaqalError
from jaqalpaq.parser import parse_jaqal_file, parse_jaqal_string
from jaqalpaq.core.result import (
    ExecutionResult,
    ProbabilisticSubcircuit,
    Readout,
)
from jaqalpaq.core.algorithm.visitor import Visitor
from jaqalpaq.core.algorithm.walkers import TraceVisitor, DiscoverSubcircuits
from jaqalpaq.core.algorithm import expand_macros, fill_in_let
from .pygsti.frontend import subcircuit_probabilities


class EmulatorWalker(TraceVisitor):
    def __init__(self, traces, probabilities):
        """(internal) Instantiates an EmulationWalker.

        Produce emulated output sampled from a given probability distribution.

        :param List[Trace] traces: the prepare_all/measure_all subcircuits
        :param List[List[Float]] probabilities: the probabilities of each outcome

        """
        super().__init__(traces)
        self.subcircuits = []
        self.res = []
        self.readout_index = 0
        for n, (sc, prob) in enumerate(zip(self.traces, probabilities)):
            self.subcircuits.append(ProbabilisticSubcircuit(sc, n, [], prob))
        # This is only valid because we must alway do measure_all.
        if self.traces:
            self.qubits = len(self.traces[0].used_qubits)

    def process_trace(self):
        subcircuit = self.subcircuits[self.index]
        nxt = choice(2 ** self.qubits, p=subcircuit.probability_by_int)
        mr = Readout(nxt, self.readout_index, subcircuit)
        self.res.append(mr)
        subcircuit._readouts.append(mr)
        self.readout_index += 1


def generate_probabilities(circ, traces):
    """(internal) Attaches noiseless result probablities to an execution result object.

    :param Circuit circ: parent circuit
    :param List[Trace] traces: The traces of circ that correspond to the prepare_all/measure_all
        subcircuits to generate probabilities of.

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    probabilities = []
    for sc in traces:
        p = subcircuit_probabilities(circ, sc)
        probs = array([(int(k[0][::-1], 2), v) for k, v in p.items()])
        probabilities.append(probs[probs[:, 0].argsort()][:, 1].copy())

    return probabilities


def run_jaqal_circuit(circuit):
    """Execute a Jaqal :class:`~jaqalpaq.core.Circuit` in a noiseless emulator.

    :param Circuit circuit: The Jaqalpaq circuit to be run.

    :rtype: ExecutionResult

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    circuit = expand_macros(fill_in_let(circuit))
    visitor = DiscoverSubcircuits()
    traces = visitor.visit(circuit)
    w = EmulatorWalker(traces, generate_probabilities(circuit, traces))
    w.visit(circuit)
    return ExecutionResult(w.subcircuits, w.res)


def run_jaqal_string(jaqal):
    """Execute a Jaqal string in a noiseless emulator.

    :param str jaqal: The literal Jaqal program text.

    :rtype: ExecutionResult

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    return run_jaqal_circuit(parse_jaqal_string(jaqal, autoload_pulses=True))


def run_jaqal_file(fname):
    """Execute a Jaqal program in a file in a noiseless emulator.

    :param str fname: The path to a Jaqal file to execute.

    :rtype: ExecutionResult

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
