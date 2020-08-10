# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from numpy.random import choice
from numpy import array
from collections import OrderedDict

from jaqalpaq import JaqalError
from jaqalpaq.parser import parse_jaqal_file, parse_jaqal_string
from jaqalpaq.core.result import ExecutionResult, Readout
from jaqalpaq.core.algorithm.visitor import Visitor
from jaqalpaq.core.algorithm.walkers import TraceVisitor, DiscoverSubcircuits
from jaqalpaq.core.algorithm import expand_macros, fill_in_let
from .pygsti.circuit import UnitarySerializedEmulator


class EmulatorWalker(TraceVisitor):
    def __init__(self, traces, backend):
        """(internal) Instantiates an EmulationWalker.

        Produce emulated output sampled from a given probability distribution.

        :param List[Trace] traces: the prepare_all/measure_all subcircuits
        :param List[List[Float]] probabilities: the probabilities of each outcome

        """
        super().__init__(traces)
        self.results = []
        self.readout_index = 0
        self.backend = backend
        # This is only valid because we must alway do measure_all.
        if self.traces:
            self.qubits = len(self.traces[0].used_qubits)

    def process_trace(self):
        subcircuit = self.backend.subcircuits[self.index]
        nxt = choice(2 ** self.qubits, p=subcircuit.probability_by_int)
        mr = Readout(nxt, self.readout_index, subcircuit)
        self.results.append(mr)
        subcircuit._readouts.append(mr)
        self.readout_index += 1


def run_jaqal_circuit(circuit, backend=None):
    """Execute a Jaqal :class:`~jaqalpaq.core.Circuit` in a noiseless emulator.

    :param Circuit circuit: The Jaqalpaq circuit to be run.
    :param backend: The backend to perform the circuit simulation/emulation.
        Defaults to UnitarySerializedEmulator.

    :rtype: ExecutionResult

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    if backend is None:
        backend = UnitarySerializedEmulator()

    circuit = expand_macros(fill_in_let(circuit))
    visitor = DiscoverSubcircuits()
    traces = visitor.visit(circuit)
    backend._bind(circuit, traces)
    w = EmulatorWalker(traces, backend)
    w.visit(circuit)
    return ExecutionResult(backend.subcircuits, w.results)


def run_jaqal_string(jaqal, backend=None):
    """Execute a Jaqal string in a noiseless emulator.

    :param str jaqal: The literal Jaqal program text.
    :param backend: The backend to perform the circuit simulation/emulation.
        Defaults to UnitarySerializedEmulator.

    :rtype: ExecutionResult

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    return run_jaqal_circuit(parse_jaqal_string(jaqal, autoload_pulses=True), backend)


def run_jaqal_file(fname, backend=None):
    """Execute a Jaqal program in a file in a noiseless emulator.

    :param str fname: The path to a Jaqal file to execute.
    :param backend: The backend to perform the circuit simulation/emulation.
        Defaults to UnitarySerializedEmulator.

    :rtype: ExecutionResult

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    return run_jaqal_circuit(parse_jaqal_file(fname, autoload_pulses=True), backend)


__all__ = [
    "run_jaqal_string",
    "run_jaqal_file",
    "run_jaqal_circuit",
]
