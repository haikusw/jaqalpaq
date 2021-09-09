# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from numpy.random import choice

from jaqalpaq.core.result import ExecutionResult, Readout
from jaqalpaq.core.result import ProbabilisticSubcircuit
from jaqalpaq.core.algorithm.walkers import TraceVisitor, DiscoverSubcircuits


class AbstractJob:
    """Abstract Jaqal Compute Job"""

    def __init__(self, backend, circuit):
        self.backend = backend
        self.circuit = circuit

    def __repr__(self):
        return f"<{type(self)} of {self.backend}>"

    def execute(self):
        """Executes the job on the backend"""
        raise NotImplementedError()


class AbstractBackend:
    """Abstract Emulator Backend"""

    def __call__(self, circ):
        """Creates a job object for circ

        :param Circuit circ: circuit to run
        """
        raise NotImplementedError()


class IndependentSubcircuitsEmulatorWalker(TraceVisitor):
    def __init__(self, traces, subcircuits):
        """(internal) Instantiates an EmulationWalker.

        Produce emulated output sampled from a given probability distribution.

        :param List[Trace] traces: the prepare_all/measure_all subcircuits
        :param List[List[Float]] probabilities: the probabilities of each outcome

        """
        super().__init__(traces)
        self.results = []
        self.readout_index = 0
        self.subcircuits = subcircuits
        # This is only valid because we must always do measure_all.
        if self.traces:
            self.qubits = len(self.traces[0].used_qubits)

    def process_trace(self):
        subcircuit = self.subcircuits[self.index]
        nxt = choice(2 ** self.qubits, p=subcircuit.probability_by_int)
        mr = Readout(nxt, self.readout_index, subcircuit)
        self.results.append(mr)
        subcircuit._readouts.append(mr)
        self.readout_index += 1


class IndependentSubcircuitsJob(AbstractJob):
    """Job for circuit with subcircuits that are independent"""

    def execute(self):
        w = IndependentSubcircuitsEmulatorWalker(self.traces, self.subcircuits)
        w.visit(self.circuit)
        return ExecutionResult(self.subcircuits, w.results)


class IndependentSubcircuitsBackend(AbstractBackend):
    """Abstract emulator backend for subcircuits that are independent"""

    def __call__(self, circ):
        """Attaches the backend to a particular circuit, creating a Job object.

        Calculates the probabilities of outcomes for every subcircuit.

        :param Circuit circ: parent circuit

        :returns IndependentSubcircuitsJob:
        """

        job = IndependentSubcircuitsJob(self, circ)
        visitor = DiscoverSubcircuits()
        job.traces = traces = visitor.visit(circ)
        subcircuits = job.subcircuits = []
        for n, tr in enumerate(traces):
            subcircuits.append(
                ProbabilisticSubcircuit(tr, n, [], self._probability(job, tr))
            )

        return job
