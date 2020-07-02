from numpy.random import choice
from numpy import array
from collections import OrderedDict

from jaqalpaq import JaqalError
from jaqalpaq.parser import parse_jaqal_file, parse_jaqal_string
from jaqalpaq.core.result import ExecutionResult
from jaqalpaq.core.algorithm.visitor import Visitor
from jaqalpaq.core.algorithm.walkers import SubcircuitsVisitor
from .pygsti.frontend import subexperiment_probabilities


class EmulatorWalker(SubcircuitsVisitor):
    def __init__(self, res):
        super().__init__(res._subexperiments)
        self.res = res

    def process_subcircuit(self):
        sc = self.subcircuits[self.s_idx]
        nxt = choice(2 ** sc.qbits, p=sc.probabilities)
        self.res._output.append((nxt, sc))
        sc._measurements.append(nxt)


def generate_probabilities(exe_res, *, prob_kwargs=None):
    """Attaches noiseless result probablities to an execution result object.

    :param exe_res: The execution result object to process.
    :param prob_kwargs: [undocumented] arguments to pass to subexperiment_probabilities

    The sub-experiments of exe_res learn their noiseless result probabilities.

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling
        ```
        numpy.random.seed(int(time.time()))
        ```
        for random behavior.

    """
    if prob_kwargs is None:
        prob_kwargs = {}

    for sc in exe_res._subexperiments:
        p = subexperiment_probabilities(exe_res._expanded_circuit, sc, **prob_kwargs)
        probs = array([(int(k[0][::-1], 2), v) for k, v in p.items()])
        sc.probabilities = probs[probs[:, 0].argsort()][:, 1].copy()


def run_jaqal_circuit(circ):
    """Execute a Jaqal Circuit in a noiseless emulator.

    :param circ: a Jaqalpaq Circuit object to be run.

    :return: An ExecutionResult object.

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling
        ```
        numpy.random.seed(int(time.time()))
        ```
        for random behavior.

    """
    res = ExecutionResult(circ)
    generate_probabilities(res)

    subexp = res._subexperiments
    for sc in subexp:
        sc._measurements = []

    res._output = []

    w = EmulatorWalker(res)
    w.visit(res._expanded_circuit)

    return res


def run_jaqal_string(jaqal):
    """Execute a Jaqal string in a noiseless emulator.

    :param jaqal: The literal Jaqal program, in a string.

    :return: An ExecutionResult object.

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling
        ```
        numpy.random.seed(int(time.time()))
        ```
        for random behavior.

    """
    return run_jaqal_circuit(parse_jaqal_string(jaqal, autoload_pulses=True))


def run_jaqal_file(fname):
    """Execute a Jaqal program in a file in a noiseless emulator.

    :param fname: a string containing a path of a Jaqal file to execute

    :return: An ExecutionResult object.

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling
        ```
        numpy.random.seed(int(time.time()))
        ```
        for random behavior.

    """
    return run_jaqal_circuit(parse_jaqal_file(fname, autoload_pulses=True))


__all__ = [
    "run_jaqal_string",
    "run_jaqal_file",
    "run_jaqal_circuit",
    "generate_probabilities",
]
