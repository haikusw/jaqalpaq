# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import itertools

import numpy
from scipy.sparse import dia_matrix

from pygsti.modelmembers.operations import ComposedOp
from pygsti.protocols import ModelFreeformSimulator

from jaqalpaq.core.algorithm.walkers import TraceSerializer
from jaqalpaq.core.result import ProbabilisticSubcircuit
from jaqalpaq.emulator.backend import IndependentSubcircuitsBackend, ExtensibleBackend

from .circuit import pygsti_circuit_from_gatelist, pygsti_circuit_from_circuit
from .model import build_noiseless_native_model, build_noisy_native_model


class pyGSTiEmulator(IndependentSubcircuitsBackend):
    """(abstract) pyGSTi emulator
    Collects common helper functions required by pyGSTi backends.
    """

    # This allows access to the pyGSTi circuit and model objects
    # used to generate probabilities.
    #
    # WARNING: THE ORDER OF QUBITS IS INVERTED RELATIVE TO JAQALPAQ!!!
    #
    KEEP_PYGSTI_OBJECTS = False


class UnitarySerializedEmulator(pyGSTiEmulator):
    """Serialized emulator using pyGSTi circuit objects

    This object should be treated as an opaque symbol to be passed to run_jaqal_circuit.
    """

    def _make_subcircuit(self, job, index, trace):
        """Generate the probabilities of outcomes of a subcircuit

        :param Trace trace: the subcircut of circ to generate probabilities for
        :return: A pyGSTi outcome dictionary.
        """

        circ = job.circuit
        n_qubits = self.get_n_qubits(circ)

        s = TraceSerializer(trace)
        pc = pygsti_circuit_from_gatelist(list(s.visit(circ)), n_qubits)
        model = build_noiseless_native_model(n_qubits, circ.native_gates)

        # Todo: currently, pyGSTi does not implement the statevector simulator.
        # We fake it here.
        op = model.circuit_operator(pc)
        if isinstance(op, ComposedOp) and (not op.factorops):
            # pyGSTi defaults to a PTM representation for an trivial product.
            # Just build the identity ourselves in that case:
            sz = 2**n_qubits
            U = dia_matrix((numpy.ones(sz), [0]), shape=(sz, sz))
        else:
            U = op.to_sparse()

        vec = U.getcol(0)

        # Todo: keep this sparse
        probs = numpy.abs(vec.toarray().flatten()) ** 2

        subcircuit = ProbabilisticSubcircuit(trace, index, [], probs)
        subcircuit.statevec = vec
        if self.KEEP_PYGSTI_OBJECTS:
            subcircuit._model = model
            subcircuit._pc = pc

        return subcircuit


class CircuitEmulator(pyGSTiEmulator):
    """Emulator using pyGSTi circuit objects

    This object should be treated as an opaque symbol to be passed to run_jaqal_circuit.
    """

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

        probs = numpy.zeros(len(prob_dict), dtype=float)
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
