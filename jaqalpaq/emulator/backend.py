# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from jaqalpaq.core.result import ProbabilisticSubcircuit


class IndependentSubcircuitsBackend:
    """Abstract Emulator Backend"""

    def _bind(self, circ, traces):
        """Attaches the backend to a particular circuit.

        Calculates the probabilities of outcomes for every subcircuit.

        :param Circuit circ: parent circuit
        :param List[Trace] traces: The traces of circ that correspond to the
            prepare_all/measure_all subcircuits to generate probabilities of.
        """

        self.traces = traces
        self.circuit = circ
        subcircuits = self.subcircuits = []
        for n, tr in enumerate(traces):
            subcircuits.append(
                ProbabilisticSubcircuit(tr, n, [], self._probability(tr))
            )
