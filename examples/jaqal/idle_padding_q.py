from jaqalpaq.qsyntax import circuit


@circuit
def idle_padding(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(3, name="q")
    with Q.subcircuit():
        with Q.parallel():
            Q.Rx(q[0], 1)
            Q.Rx(q[1], 1.2)
