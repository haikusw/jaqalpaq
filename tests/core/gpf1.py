from jaqalpaq.core import GateDefinition, Parameter, ParamType


NATIVE_GATES = dict(
    testgate=GateDefinition("testgate", [Parameter("q0", ParamType.QUBIT)])
)
