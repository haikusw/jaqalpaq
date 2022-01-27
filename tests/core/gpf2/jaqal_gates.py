from jaqalpaq.core import GateDefinition, Parameter, ParamType


ALL_GATES = dict(
    testgate=GateDefinition(
        "testgate", [Parameter("q0", ParamType.QUBIT), Parameter("q1", ParamType.QUBIT)]
    )
)
