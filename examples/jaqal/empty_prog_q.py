from jaqalpaq.qsyntax import circuit


@circuit
def empty_loop(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(1, name="q")
    with Q.subcircuit():
        pass
