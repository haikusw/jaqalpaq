# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import pygsti
import numpy as np

from jaqalpaq import JaqalError


class JaqalOpFactory(pygsti.obj.OpFactory):
    """Jaqal gate factory
    Takes a function describing a Jaqal gate (with identical call signature) and optional
      JaqalPaq gate definition, and creates a pyGSTi operator factory appropriate for
      describing that gate in a noise model.
    """

    def __init__(self, fun, gate=None, evotype="densitymx", **kwargs):
        if "evotype" not in kwargs:
            kwargs["evotype"] = "densitymx"

        if gate is None:
            # Idle gate
            kwargs["dim"] = 4
        else:
            kwargs["dim"] = 4 ** len(gate.quantum_parameters)

        pygsti.obj.OpFactory.__init__(self, **kwargs)
        self.jaqal_gate = gate
        self.jaqal_fun = fun

    def create_object(self, args=None, sslbls=None):
        if self.jaqal_gate is None:
            (duration,) = args
            # Idle gate
            return pygsti.obj.StaticDenseOp(self.jaqal_fun(None, duration))

        n_arg = 0
        n_ssl = 0
        argv = []

        for param in self.jaqal_gate.parameters:
            if param.classical:
                argv.append(args[n_arg])
                n_arg += 1
            else:
                # We do not allow qubit-specific models (yet)
                argv.append(None)
                n_ssl += 1

        return pygsti.obj.StaticDenseOp(self.jaqal_fun(*argv))


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

    return pygsti.obj.StaticDenseOp(fun(*[None for i in range(quantum_args)]))


def pygsti_unitary(g):
    """Ideal unitary action of the gate with pyGSTi special casing.

    :param parms: A list of all classical arguments to the gate.
    :return: The ideal unitary action of the gate on its target qubits, or an
        identity gate on the target qubit.
    """

    def _unitary_fun(parms):
        if parms:
            return g.ideal_unitary(*parms)
        else:
            return np.identity(2 ** len(g.quantum_parameters))

    return _unitary_fun


def build_ideal_unitaries_dict(gates, unitaries, availability):
    """Build a dictionary of ideal unitaries suitable for pygsti model creation.
    Adds key names of the form GJ<gate name> for each Jaqal gate

    :param gates: a dictionary of Jaqal gates
    :param unitaries: the dictionary to add to
    :param availability: the availability dictionary
    """
    for g in gates.values():
        # Skip gates without defined action
        if g.ideal_unitary is None:
            continue

        if len(g.quantum_parameters) == 0:
            raise JaqalError(f"{g.name} not supported")

        if len(g.classical_parameters) > 0:
            obj = pygsti_unitary(g)
        else:
            obj = g.ideal_unitary()

        name = f"GJ{g.name}"
        unitaries[name] = obj

        if len(g.quantum_parameters) > 1:
            availability[name] = "all-permutations"


def build_noiseless_native_model(n_qubits, gates):
    """Build a noise model for each Jaqal gate

    :param gates: a dictionary of Jaqal gates
    :param n_qubits: the number of qubits in the model
    :return: a pyGSTi noise model object
    """
    unitaries = {}
    availability = {}

    build_ideal_unitaries_dict(gates, unitaries, availability)

    unitaries["Gidle"] = lambda *args: np.identity(2)

    target_model = pygsti.construction.build_localnoise_model(
        nQubits=n_qubits,
        gate_names=list(unitaries.keys()),
        nonstd_gate_unitaries=unitaries,
        availability=availability,
        qubit_labels=list(range(n_qubits)),
        parameterization="static unitary",
    )

    return target_model
