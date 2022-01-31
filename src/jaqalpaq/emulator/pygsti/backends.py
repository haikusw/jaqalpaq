# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from numpy import zeros
import itertools

import pygsti
from pygsti.modelmembers.states import ComputationalBasisState
from pygsti.modelmembers.povms import ComputationalBasisPOVM
from pygsti.modelmembers.operations import opfactory, ComposedOp
from pygsti.processors.processorspec import QubitProcessorSpec

from jaqalpaq.core.algorithm.walkers import TraceSerializer
from jaqalpaq.emulator.backend import IndependentSubcircuitsBackend

from .circuit import pygsti_circuit_from_gatelist, pygsti_circuit_from_circuit
from .model import (
    build_noiseless_native_model,
    pygsti_independent_noisy_gate,
    JaqalOpFactory,
    DummyUnitaryGate,
)


class pyGSTiEmulator(IndependentSubcircuitsBackend):
    """(abstract) pyGSTi emulator
    Collects common helper functions required by pyGSTi backends.
    """

    def _probs_from_model(self, model, pc):
        prob_dict = model.probabilities(pc)
        probs = zeros(len(prob_dict), dtype=float)
        for k, v in prob_dict.items():
            k = int(k[0][::-1], 2)
            probs[k] = v

        return probs


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


class AbstractNoisyNativeEmulator(CircuitEmulator):
    """(abstract) Noisy emulator using pyGSTi circuit objects

    Provides helper functions to make the generation of a noisy native model simpler.

    Every gate to be emulated should have a corresponding gate_{name} and
      gateduration_{name} method defined.  These will be automatically converted into
      pyGSTi-appropriate objects for model construction.  See build_model for more
      details.
    """

    def __init__(self, n_qubits, stretched_gates=None, **kwargs):
        """(abstract) Perform part of the construction of a noisy model.

        :param n_qubits: The number of qubits to simulate
        :param stretched_gates: (default False)  Add stretched gates to the model:
          - If None, do not modify the gates.
          - If 'add', add gates with '_stretched' appended that take an extra parameter,
            a stretch factor.
          - Otherwise, stretched_gates must be the numerical stretch factor that is
            applied to all gates (no extra stretched gates are added
        """
        self.n_qubits = n_qubits
        self.stretched_gates = stretched_gates
        model, durations = self.build_model()
        super().__init__(model=model, gate_durations=durations, **kwargs)

    def build_model(self):
        """
        Parse the dictionary of the **current** class for entries named gate_{name},
          convert them to pyGSTi-appropriate objects using pygsti_independent_noisy_gate,
          and then submit them to build_localnoise_model to produce a pyGSTi local noise
          model.  Furthermore, collect corresponding gateduration_{name} objects into a
          dictionary.

        Both the gate and gateduration functions must take a signature identical to
          each other and their corresponding Jaqal gate.  Currently, all qubit parameters
          will be passed None, but future versions may pass a description of the qubit
          to simulate (allowing qubit-dependent noise models).

        If _stretched gates are to be automatically supported, the gate_ and
          gateduration_ methods must take an optional parameter stretch with default value
          of 1, giving the stretched version of the gate.  The stretched version of the
          Jaqal gates must exist in jaqal_gates.  The stretch factor is the final
          parameter of the gate.

        :return tuple: of pyGSTi local noise model and dictionary (of duration functions)
        """
        gates = {}
        durations = {}
        availability = {}
        jaqal_gates = self.jaqal_gates
        dummy_unitaries = {}

        if self.stretched_gates not in (None, "add"):

            def do_stretch(unstretched):
                return lambda *args: unstretched(*args, stretch=self.stretched_gates)

        for gate_name in type(self).__dict__:
            if not gate_name.startswith("gate_"):
                continue

            name = gate_name[5:]
            pygsti_name = f"GJ{name}"
            jaqal_gate = self.jaqal_gates[name]
            func = getattr(self, gate_name)
            dur = getattr(self, f"gateduration_{name}")

            num_qubits = len(jaqal_gate.quantum_parameters)
            dummy_unitary = DummyUnitaryGate(num_qubits)

            if self.stretched_gates == "add":
                stretched_pygsti_name = f"{pygsti_name}_stretched"
                stretched_name = f"{name}_stretched"
                durations[stretched_name] = dur
                gates[stretched_pygsti_name] = pygsti_independent_noisy_gate(
                    self.jaqal_gates[stretched_name], func
                )
                if num_qubits > 1:
                    availability[stretched_pygsti_name] = "all-permutations"
                else:
                    availability[stretched_pygsti_name] = [
                        (sslbl,) for sslbl in range(self.n_qubits)
                    ]

                dummy_unitaries[stretched_pygsti_name] = dummy_unitary(None)
            elif self.stretched_gates == None:
                pass
            else:
                func = do_stretch(func)
                dur = do_stretch(dur)

            durations[name] = dur
            gates[pygsti_name] = pygsti_independent_noisy_gate(jaqal_gate, func)

            if num_qubits > 1:
                availability[pygsti_name] = "all-permutations"
            else:
                availability[pygsti_name] = [(sslbl,) for sslbl in range(self.n_qubits)]

            dummy_unitaries[pygsti_name] = dummy_unitary(None)

        gates["Gidle"] = JaqalOpFactory(self.idle)
        availability["Gidle"] = [(sslbl,) for sslbl in range(self.n_qubits)]

        dummy_unitary = DummyUnitaryGate(1)
        dummy_unitaries["Gidle"] = dummy_unitary(None)

        # Make pspec with dummy unitaries of correct size (regardless of unitary or process mx)
        pspec = QubitProcessorSpec(
            self.n_qubits,
            gate_names=list(gates.keys()),
            nonstd_gate_unitaries=dummy_unitaries,
            availability=availability,
        )

        target_model = pygsti.models.LocalNoiseModel(
            pspec,
            gatedict=gates,
            prep_layers=[
                ComputationalBasisState([0] * pspec.num_qubits, evotype="densitymx")
            ],
            povm_layers=[ComputationalBasisPOVM(pspec.num_qubits, evotype="densitymx")],
            evotype="densitymx",
            simulator="matrix",
        )

        return target_model, durations

    def set_defaults(self, kwargs, **values):
        """Helper function to set default values.
        For every value passed as a keyword argument or in kwargs, set it in the object's
          namespace, with values in kwargs taking precedence.

        :param kwargs: a dictionary of your function's keyword arguments
        """
        for k, v in values.items():
            setattr(self, k, kwargs.pop(k, v))

    @staticmethod
    def _curry(params, *ops):
        """Helper function to make defining related gates easier.
        Curry every function in ops, using the signature description in params.  For
          every non-None entry of params, pass that value to the function.

        :param params: List of parameters to pass to each op in ops, with None allowing
          passthrough of values in the new function
        :param ops: List of functions to curry
        :return List[functions]: A list of curried functions
        """

        def _inner(op):
            def newop(self, *args, **kwargs):
                args = iter(args)
                argv = [next(args) if param is None else param for param in params]
                argv.extend(args)
                return op(self, *argv, **kwargs)

            return newop

        newops = []
        for op in ops:
            newops.append(_inner(op))

        return newops
