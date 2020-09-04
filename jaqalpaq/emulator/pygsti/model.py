# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import pygsti
import numpy as np

from jaqalpaq import JaqalError


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


def build_noiseless_native_model(registers, gates):
    """Build a noise model for each Jaqal gate

    :param gates: a dictionary of Jaqal gates
    :param register: the Jaqal registers that the gates may act on
    :return: a pyGSTi noise model object
    """
    unitaries = {}
    availability = {}

    fundamental_registers = [r for r in registers.values() if r._alias_from is None]
    if len(fundamental_registers) > 1:
        print(
            "Warning:  More than one physical register name in use; ordering may be borked."
        )
    physical_qubit_list = []
    for r in fundamental_registers:
        for q in r:
            physical_qubit_list.append(q._name)

    num_qubits = len(physical_qubit_list)

    build_ideal_unitaries_dict(gates, unitaries, availability)

    unitaries["Gidle"] = lambda *args: np.identity(2)

    target_model = pygsti.construction.build_localnoise_model(
        nQubits=num_qubits,
        gate_names=list(unitaries.keys()),
        nonstd_gate_unitaries=unitaries,
        availability=availability,
        qubit_labels=physical_qubit_list,
        parameterization="static unitary",
    )

    return target_model
