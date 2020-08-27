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


def build_noiseless_native_model(registers, gates):
    """Builds a noise model for each Jaqal gate

    :param register: the Jaqal registers that the gates may act on
    :param gates: a dictionary of Jaqal gates
    :return: a pyGSTi noise model object
    """
    gate_names = []
    unitaries = {}
    availability = {}

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
        gate_names.append(name)
        unitaries[name] = obj

        if len(g.quantum_parameters) > 1:
            availability[name] = "all-permutations"

    gate_names.append("Gidle")
    unitaries["Gidle"] = lambda *args: np.identity(2)

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

    target_model = pygsti.construction.build_localnoise_model(
        nQubits=num_qubits,
        gate_names=gate_names,
        nonstd_gate_unitaries=unitaries,
        availability=availability,
        qubit_labels=physical_qubit_list,
        parameterization="static unitary",
    )

    return target_model
