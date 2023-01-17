from jaqalpaq.qsyntax import circuit


@circuit
def zero_loop(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(1, name="q")
    with Q.subcircuit():
        with Q.loop(0):
            Q.Px(q[0])
