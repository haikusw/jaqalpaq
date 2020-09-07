# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from numpy import array

import pygsti

from jaqalpaq.core.algorithm.walkers import TraceSerializer
from jaqalpaq.emulator.backend import IndependentSubcircuitsBackend

from .circuit import pygsti_circuit_from_gatelist, pygsti_circuit_from_circuit
from .model import build_noiseless_native_model


class pyGSTiEmulator(IndependentSubcircuitsBackend):
    """(abstract) pyGSTi emulator
    Collects common helper functions required by pyGSTi backends.
    """

    ZERO_CUTOFF = 1e-13

    def _probs_from_model(self, model, pc):
        res = []
        for k, v in model.probs(pc).items():
            if (v < 0) and (v > -self.ZERO_CUTOFF):
                v = 0
            res.append((int(k[0][::-1], 2), v))

        probs = array(res)
        return probs[probs[:, 0].argsort()][:, 1].copy()


class UnitarySerializedEmulator(pyGSTiEmulator):
    """Serialized emulator using pyGSTi circuit objects

    This object should be treated as an opaque symbol to be passed to run_jaqal_circuit.
    """

    def _probability(self, job, trace):
        """Generate the probabilities of outcomes of a subcircuit

        :param Trace trace: the subcircut of circ to generate probabilities for
        :return: A pyGSTi outcome dictionary.
        """

        circ = job.circuit
        try:
            (register,) = circ.fundamental_registers()
        except ValueError:
            raise NotImplementedError("Multiple fundamental registers unsupported.")

        n_qubits = register.size

        s = TraceSerializer(trace)
        pc = pygsti_circuit_from_gatelist(list(s.visit(circ)), n_qubits)
        model = build_noiseless_native_model(n_qubits, circ.native_gates)
        return self._probs_from_model(model, pc)


class CircuitEmulator(pyGSTiEmulator):
    """Emulator using pyGSTi circuit objects

    This object should be treated as an opaque symbol to be passed to run_jaqal_circuit.
    """

    def __init__(self, *args, model=None, gate_durations=None, **kwargs):
        self.model = model
        self.gate_durations = gate_durations if gate_durations is not None else {}
        super().__init__(*args, **kwargs)

    def _probability(self, job, trace):
        """Generate the probabilities of outcomes of a subcircuit

        :param Trace trace: the subcircut of circ to generate probabilities for
        :return: A pyGSTi outcome dictionary.
        """

        pc = pygsti_circuit_from_circuit(
            job.circuit, trace=trace, durations=self.gate_durations
        )
        return self._probs_from_model(self.model, pc)
