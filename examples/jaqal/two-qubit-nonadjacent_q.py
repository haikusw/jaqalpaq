from jaqalpaq.qsyntax import circuit


@circuit
def two_qubit_nonadjacent(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(3, name="q")
    with Q.subcircuit():
        Q.MS(q[0], q[2], 0.123, 0.987)
