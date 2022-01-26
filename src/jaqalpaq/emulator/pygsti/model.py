# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import numpy as np

from pygsti.modelmembers.operations import OpFactory, StaticUnitaryOp, StaticArbitraryOp
from pygsti.modelmembers.states import ComputationalBasisState
from pygsti.modelmembers.povms import ComputationalBasisPOVM
from pygsti.models import LocalNoiseModel
from pygsti.processors import QubitProcessorSpec, UnitaryGateFunction

from jaqalpaq.error import JaqalError


class JaqalOpFactory(OpFactory):
    """Jaqal gate factory
    Takes a function describing a Jaqal gate (with identical call signature) and optional
      JaqalPaq gate definition, and creates a pyGSTi operator factory appropriate for
      describing that gate in a noise model.
    """

    def __init__(self, fun, gate=None, pass_args=("classical", "quantum"), **kwargs):
        """Construct a Jaqal gate factory.

        :param fun: Function generating the specified unitary/process matrix
        :param gate: Optional Jaqal gate. If None, this probably specifies an idle gate.
        :param evotype: When True (default), pass quantum arguments to fun;
            if False, pass classical arguments only (typically the case for ideal unitaries)
        :return: a PyGSTi OpFactory describing the Jaqal gate
        """
        if "evotype" not in kwargs:
            kwargs["evotype"] = "densitymx"

        self.num_qubits = 1 if gate is None else len(gate.quantum_parameters)
        kwargs["state_space"] = self.num_qubits

        OpFactory.__init__(self, **kwargs)
        self.jaqal_gate = gate
        self.jaqal_fun = fun
        self.pass_args = pass_args

    def create_object(self, args=None, sslbls=None):
        if self.jaqal_gate is None:
            (duration,) = args
            # Idle gate
            mat = np.array(self.jaqal_fun(None, duration))
        else:
            n_arg = 0
            n_ssl = 0
            argv = []
            ssls = []

            for param in self.jaqal_gate.parameters:
                if param.classical and "classical" in self.pass_args:
                    argv.append(args[n_arg])
                    n_arg += 1
                elif "quantum" in self.pass_args:
                    # We do not allow qubit-specific models (yet)
                    argv.append(None)
                    n_ssl += 1

            mat = np.array(self.jaqal_fun(*argv))

        if mat.shape == (4**self.num_qubits, 4**self.num_qubits):
            return StaticArbitraryOp(mat, evotype=self._evotype)

        return StaticUnitaryOp(mat, evotype=self._evotype)


class DummyUnitaryGate(UnitaryGateFunction):
    def __init__(self, num_qubits):
        self.num_qubits = num_qubits
        self.shape = (2**self.num_qubits, 2**self.num_qubits)

    def __call__(self, arg):
        return -1 * np.eye(2**self.num_qubits, dtype="complex")


def pygsti_independent_noisy_gate(gate, fun):
    """Generates a pyGSTi-compatible wrapper for a noisy gate without crosstalk.

    This is a convenience wrapper, and currently does not support qubit-dependent errors.

    :param gate: The Jaqalpaq gate definition object describing the gate.
    :param fun: The Python function taking parameters in the order of the Jaqal gate and
        returning the process matrix in the Pauli basis.
    :return: The StaticDenseOp or OpFactory object
    """

    fact = False
    quantum_args = 0
    for param in gate.parameters:
        if param.classical:
            fact = True
            break
        quantum_args += 1

    if fact:
        return JaqalOpFactory(fun, gate)

    return StaticArbitraryOp(fun(*[None for i in range(quantum_args)]))


def pygsti_ideal_unitary(gate):
    """Ideal unitary action of the gate with pyGSTi special casing.

    :param gate: The Jaqalpaq gate definition object describing the gate.
    """

    def _unitary_fun(*parms):
        """
        :param parms: A list of all classical arguments to the gate.
        :return: The ideal unitary action of the gate on its target qubits, or an
        identity gate on the target qubit.
        """
        if parms:
            return gate.ideal_unitary(*parms)
        else:
            return np.identity(2 ** len(gate.quantum_parameters), "complex")

    return _unitary_fun


def build_processor_spec(n_qubits, gates):
    """Build a ProcessorSpec of ideal unitaries suitable for pygsti model creation.
    Adds key names of the form GJ<gate name> for each Jaqal gate

    :param n_qubits: the number of qubits in the model
    :param gates: a dictionary of Jaqal gates
    :return: PyGSTi ProcessorSpec to be used in model creation
    """
    unitaries = {}
    dummy_unitaries = {}
    availability = {}
    for g in gates.values():
        # Skip gates without defined action
        if g.ideal_unitary is None:
            continue

        if len(g.quantum_parameters) == 0:
            raise JaqalError(f"{g.name} not supported")

        if len(g.classical_parameters) > 0:
            obj = pygsti_ideal_unitary(g)
        else:
            obj = g.ideal_unitary()

        # Cast to either a PyGSTi StaticUnitaryOp or OpFactory to avoid autoconstruction logic
        if callable(obj):
            # For the ideal unitary, only pass classical arguments to underlying function
            obj = JaqalOpFactory(obj, gate=g, pass_args=("classical",))
        else:
            obj = StaticUnitaryOp(obj, evotype="densitymx")

        name = f"GJ{g.name}"
        unitaries[name] = obj

        if len(g.quantum_parameters) > 1:
            availability[name] = "all-permutations"
        else:
            availability[name] = [(sslbl,) for sslbl in range(n_qubits)]

        dummy_unitary = DummyUnitaryGate(len(g.quantum_parameters))
        dummy_unitaries[name] = dummy_unitary(None)

    if "Gidle" not in unitaries:
        unitaries["Gidle"] = JaqalOpFactory(lambda *args: np.identity(2, "complex"))
        availability["Gidle"] = [(sslbl,) for sslbl in range(n_qubits)]

        dummy_unitary = DummyUnitaryGate(1)
        dummy_unitaries["Gidle"] = dummy_unitary(None)

    pspec = QubitProcessorSpec(
        n_qubits,
        gate_names=list(unitaries.keys()),
        nonstd_gate_unitaries=dummy_unitaries,
        availability=availability,
    )

    return pspec, unitaries


def build_noiseless_native_model(n_qubits, gates, evotype="densitymx"):
    """Build a noise model for each Jaqal gate

    :param n_qubits: the number of qubits in the model
    :param gates: a dictionary of Jaqal gates
    :param evotype: pyGSTi evolution type
    :return: a pyGSTi noise model object
    """
    pspec, gatedict = build_processor_spec(n_qubits, gates)

    target_model = LocalNoiseModel(
        pspec,
        gatedict,
        prep_layers=[ComputationalBasisState([0] * pspec.num_qubits, evotype=evotype)],
        povm_layers=[ComputationalBasisPOVM(pspec.num_qubits, evotype=evotype)],
        evotype=evotype,
    )

    return target_model
