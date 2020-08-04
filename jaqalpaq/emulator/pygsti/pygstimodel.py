# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import pygsti
import numpy as np

from jaqalpaq import JaqalError


def build_noiseless_native_model(
    registers, gates,
):
    """Builds a noise model for each Jaqal gate

    :param register: the Jaqal registers that the gates may act on
    :param gates: a dictionary of Jaqal gates
    :return: a pyGSTi noise model object
    """
    gate_names = []
    unitaries = {}
    availability = {}

    for g in gates.values():
        name = f"G{g.name.lower()}"
        gate_names.append(name)

        if len(g.quantum_parameters) == 0:
            # AER: We are special casing prepare and measurements right now
            if g.name in ("prepare_all", "measure_all"):
                unitaries[name] = np.identity(2)
            else:
                raise JaqalError(f"{g.name} not supported")
            continue

        if len(g.classical_parameters) > 0:
            unitaries[name] = g._ideal_unitary_pygsti
        else:
            unitaries[name] = g.ideal_unitary()

        if len(g.quantum_parameters) > 1:
            availability[name] = "all-permutations"

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
