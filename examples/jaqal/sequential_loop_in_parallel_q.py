from jaqalpaq.qsyntax import circuit


@circuit
def empty_loop(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(2, name="q")
    with Q.subcircuit():
        with Q.parallel():
            with Q.loop(1):
                Q.Px(q[0])
