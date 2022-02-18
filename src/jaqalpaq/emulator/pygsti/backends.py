# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import itertools

from numpy import zeros

from pygsti.modelmembers.operations import ComposedOp
from pygsti.protocols import ModelFreeformSimulator

from jaqalpaq.core.algorithm.walkers import TraceSerializer
from jaqalpaq.core.result import ProbabilisticSubcircuit
from jaqalpaq.emulator.backend import IndependentSubcircuitsBackend, ExtensibleBackend

from .circuit import pygsti_circuit_from_circuit
from .model import build_noisy_native_model


class CircuitEmulator(IndependentSubcircuitsBackend):
    """Emulator using pyGSTi circuit objects

    This object should be treated as an opaque symbol to be passed to run_jaqal_circuit.
    """

    # This allows access to the pyGSTi circuit and model objects
    # used to generate probabilities.
    #
    # WARNING: THE ORDER OF QUBITS IS INVERTED RELATIVE TO JAQALPAQ!!!
    #
    KEEP_PYGSTI_OBJECTS = False

    def __init__(self, *args, model=None, gate_durations=None, **kwargs):
        self.model = model
        self.gate_durations = gate_durations if gate_durations is not None else {}
        super().__init__(*args, **kwargs)

    def _make_subcircuit(self, job, index, trace):
        """Generate the probabilities of outcomes of a subcircuit

        :param Trace trace: the subcircut of circ to generate probabilities for
        :return: A pyGSTi outcome dictionary.
        """

        circ = job.circuit
        n_qubits = self.get_n_qubits(circ)

        pc = pygsti_circuit_from_circuit(
            circ, trace=trace, durations=self.gate_durations, n_qubits=n_qubits
        )

        model = self.model
        mfs = ModelFreeformSimulator(None)
        rho, prob_dict = mfs.compute_final_state(model, pc, include_probabilities=True)

        probs = zeros(len(prob_dict), dtype=float)
        for k, v in prob_dict.items():
            probs[int(k, 2)] = v

        subcircuit = ProbabilisticSubcircuit(trace, index, [], probs)
        subcircuit.rho = rho
        if self.KEEP_PYGSTI_OBJECTS:
            subcircuit._model = model
            subcircuit._pc = pc

        return subcircuit


class AbstractNoisyNativeEmulator(ExtensibleBackend, CircuitEmulator):
    """(abstract) Noisy emulator using pyGSTi circuit objects

    Provides helper functions to make the generation of a noisy native model simpler.

    Every gate to be emulated should have a corresponding gate_{name} and
      gateduration_{name} method defined.  These will be automatically converted into
      pyGSTi-appropriate objects for model construction.  See build_model for more
      details.
    """

    def build_model(self):
        return build_noisy_native_model(
            self.jaqal_gates,
            self.collect_gate_models(),
            self.idle,
            self.n_qubits,
            stretched_gates=self.stretched_gates,
        )
