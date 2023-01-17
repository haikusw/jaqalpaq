from jaqalpaq.qsyntax import circuit


@circuit
def parallel_block_in_sequential_loop(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(2, name="q")
    with Q.subcircuit():
        with Q.loop(2):
            with Q.parallel():
                Q.Sx(q[0])
                Q.Sx(q[1])
