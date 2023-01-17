from jaqalpaq.qsyntax import circuit


@circuit
def prepare_measure_equiv(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(1, name="q")

    with Q.subcircuit():
        Q.Sx(q[0])
        Q.Sx(q[0])

    with Q.subcircuit():
        with Q.loop(7):
            Q.Sx(q[0])

    with Q.subcircuit():
        Q.Sy(q[0])
