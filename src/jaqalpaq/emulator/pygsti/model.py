# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import numpy as np

from pygsti.modelmembers.operations import (
    OpFactory,
    StaticUnitaryOp,
    StaticArbitraryOp,
)
from pygsti.modelmembers.povms import ComputationalBasisPOVM
from pygsti.modelmembers.states import ComputationalBasisState
from pygsti.models import LocalNoiseModel
from pygsti.processors import QubitProcessorSpec
from pygsti.baseobjs import UnitaryGateFunction

from jaqalpaq.error import JaqalError


def pygsti_gate_name(gate):
    """Returns the canonical pyGSTi gate name of a Jaqal gate."""
    return f"GJ{gate.name}"


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
            kwargs["evotype"] = "default"

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


def build_processor_spec(n_qubits, gates, evotype="default"):
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
            obj = JaqalOpFactory(obj, gate=g, pass_args=("classical",), evotype=evotype)
        else:
            obj = StaticUnitaryOp(obj, evotype=evotype)

        pygsti_name = pygsti_gate_name(g)
        unitaries[pygsti_name] = obj

        if len(g.quantum_parameters) > 1:
            availability[pygsti_name] = "all-permutations"
        else:
            availability[pygsti_name] = [(sslbl,) for sslbl in range(n_qubits)]

        dummy_unitary = DummyUnitaryGate(len(g.quantum_parameters))
        dummy_unitaries[pygsti_name] = dummy_unitary(None)

    if "Gidle" not in unitaries:
        unitaries["Gidle"] = JaqalOpFactory(
            lambda *args: np.identity(2, "complex"), evotype=evotype
        )
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


def build_noiseless_native_model(n_qubits, gates, evotype="statevec"):
    """Build a (noiseless) noise model for each Jaqal gate

    :param n_qubits: the number of qubits in the model
    :param gates: a dictionary of Jaqal gates
    :param evotype: the pyGSTi evolution type to use for the model.  The default is
        "statevec", which is sufficient for noiseless simulation.
    :return: a pyGSTi noise model object
    """
    pspec, gatedict = build_processor_spec(n_qubits, gates, evotype=evotype)

    target_model = LocalNoiseModel(
        pspec,
        gatedict,
        prep_layers=[ComputationalBasisState([0] * pspec.num_qubits, evotype=evotype)],
        povm_layers=[ComputationalBasisPOVM(pspec.num_qubits, evotype=evotype)],
        evotype=evotype,
    )

    if evotype == "statevec":
        import warnings

        warnings.warn('Setting sim="matrix".  Emulation will be SLOW.')
        target_model.sim = "matrix"

    return target_model


def build_noisy_native_model(
    jaqal_gates,
    gate_models,
    idle_model,
    n_qubits,
    stretched_gates=None,
    evotype="default",
):
    """
    :param jaqal_gates: A dictionary of JaqalPaq gate objects (with their names as keys).
      This must be a superset of the gates to process in gate_models.
    :param gate_models: A dictionary of (gatemodel, gateduration) pairs (with Jaqal gate
      names as keys).  gatemodel is a function that is passed to
      pygsti_independent_noisy_gate, which converts it to a pyGSTi-compatible expression
      of the noisy gate.  gateduration is a function that (just like its sibling,
      gatemodel) takes the same arguments as the corresponding Jaqal gate, and returns
      the duration that gate will take.
    :param idle_model: A function that produces the behavior of the system when idling
      for a given duration.
    :param n_qubits: The number of qubits the quantum computer is running
    :param stretched_gates: Whether and how to add gate stretching.  Gate stretching is
      a mechanism to create (or modify) Jaqal gates to provide access to an additional
      nonnegative real-valued parameter called the "stretch factor" that causes the
      duration of the gate to be multiplied by this factor.  This argument is passed as
      the last parameter to the jaqal gate.  Both gateduration, and gatemodel functions
      must also accept this parameter as a named, OPTIONAL last positional parameter,
      `stretch`.  This is a convenience behavior to avoid the need to manually modify
      and/or duplicate all the Jaqal gates, and gatemodel and gateduration functions.
      If set to None (the default), do not add or modify the gates to provide stretched
      gates.  If set to "add", each gate that ends in `_streched` will also use the
      (gatemodel, gateduration) pair without the `_stretched` suffix. There MUST BE
      GATES with the `_stretched` suffix already in jaqal_gates (see
      jaqalpaq.core.stretch for a mechanism to automate the creation of those Jaqal gate
      objects).  If set to any other value, that value is passed as the keyword
      parameter "stretch", to both gate and gateduration, (i.e., uniformly all gates are
      given the same stretch factor, and the API exposed to the Jaqal code is not
      modified in any way, only the behavior).
    :param evotype: What kind of object pyGSTi simulates (e.g., density matrix or state
      vector).  See pyGSTi documentation for details.

    :return tuple: of pyGSTi local noise model and dictionary (of duration functions)
    """
    gates = {}
    durations = {}
    availability = {}
    dummy_unitaries = {}

    do_stretch = lambda x: x
    if stretched_gates is None:
        patterns = ("{}",)
    elif stretched_gates == "add":
        patterns = ("{}", "{}_stretched")
    else:
        if (float(stretched_gates) != stretched_gates) or (stretched_gates < 0):
            raise JaqalError("stretched_gates should be a nonnegative real number.")

        patterns = ("{}",)

        def do_stretch(unstretched):
            return lambda *args: unstretched(*args, stretch=stretched_gates)

    for name, (func, dur) in gate_models.items():
        jaqal_gate = jaqal_gates[name]
        pygsti_name = pygsti_gate_name(jaqal_gate)

        gate_qubit_count = len(jaqal_gate.quantum_parameters)
        dummy_unitary = DummyUnitaryGate(gate_qubit_count)

        func = do_stretch(func)
        dur = do_stretch(dur)

        for pattern in patterns:
            pygsti_name_spec = pattern.format(pygsti_name)
            name_spec = pattern.format(name)
            jaqal_gate_spec = jaqal_gates[name]

            durations[name_spec] = dur
            # This calls the SAME FUNCTION for both ${NAME}_stretched and
            # ${NAME} .  CONVENTION (and the definition of ${NAME}_stretched
            # in jaqal_gates) determines what the additional parameters are.
            gates[pygsti_name_spec] = pygsti_independent_noisy_gate(
                jaqal_gates[name_spec], func
            )

            if gate_qubit_count > 1:
                availability[pygsti_name_spec] = "all-permutations"
            else:
                availability[pygsti_name_spec] = [(sslbl,) for sslbl in range(n_qubits)]

            dummy_unitaries[pygsti_name_spec] = dummy_unitary(None)

    gates["Gidle"] = JaqalOpFactory(idle_model)
    availability["Gidle"] = [(sslbl,) for sslbl in range(n_qubits)]

    dummy_unitary = DummyUnitaryGate(1)
    dummy_unitaries["Gidle"] = dummy_unitary(None)

    # Make pspec with dummy unitaries of correct size (regardless of unitary or process mx)
    pspec = QubitProcessorSpec(
        n_qubits,
        gate_names=list(gates.keys()),
        nonstd_gate_unitaries=dummy_unitaries,
        availability=availability,
    )

    target_model = LocalNoiseModel(
        pspec,
        gatedict=gates,
        prep_layers=[ComputationalBasisState([0] * pspec.num_qubits, evotype=evotype)],
        povm_layers=[ComputationalBasisPOVM(pspec.num_qubits, evotype=evotype)],
        evotype=evotype,
        simulator="matrix",
    )

    return target_model, durations
