from jaqalpaq.qsyntax import circuit


@circuit
def empty_parallel(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(2, name="q")
    with Q.subcircuit():
        with Q.parallel():
            pass
