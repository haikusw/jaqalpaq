# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from .parameter import Parameter, ParamType
from .gatedef import IdleGateDefinition


def stretched_gates(gates, *, suffix=None, update=False):
    """Generate stretched GateDefinitions from parent GateDefinitions

    :param gates: A dictionary of GateDefinition objects representing the gates
      available.  The keys are ignored, and the intrinsic gate names are processed.
    :param suffix str: (optional) A suffix to append to the names of the gates.
    :param update: (default False) If True, return gates after updating with the new
      stretched gates.

    :return dict: The stretched gates, with keys being the gate names.

    If an idle gate is passed in via gates, a stretched gate for its parent gate is
    automatically generated.
    """
    new_gates = {}
    for gate in gates.values():
        name = gate.name
        if name in new_gates:
            # We already processed the idle gate for this gate,
            # and generated the parent gate.
            continue

        if isinstance(gate, IdleGateDefinition):
            add_idle = True
            gate = gate._parent_def
        else:
            add_idle = False

        if suffix:
            new_name = gate.name + suffix
        else:
            new_name = None

        parameters = gate.parameters.copy()
        parameters.append(Parameter("stretch", ParamType.FLOAT))

        if gate.ideal_unitary:
            # Drop the last argument, which is the stretch factor
            ideal_unitary = lambda *args: gate.ideal_unitary(args[:-1])
        else:
            ideal_unitary = None

        new_gate = gate.copy(
            name=new_name, parameters=parameters, ideal_unitary=ideal_unitary
        )

        new_gates[new_name] = new_gate
        if add_idle:
            new_name = name + suffix
            new_gate = IdleGateDefinition(new_gate, name=new_name)
            new_gates[new_name] = new_gate

    if update:
        gates.update(new_gates)
        return gates
    return new_gates
