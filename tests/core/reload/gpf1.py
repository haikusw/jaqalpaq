from jaqalpaq.core import GateDefinition, Parameter, ParamType


class jaqal_gates:
    ALL_GATES = dict(
        testgate=GateDefinition("reloadedtestgate", [Parameter("q0", ParamType.QUBIT)])
    )
