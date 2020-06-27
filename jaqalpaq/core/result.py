from collections import OrderedDict

from .algorithm import fill_in_let, expand_macros
from .algorithm.walkers import *


class Subexperiment(Subcircuit):
    """Represents a prepare/measure portion of a Jaqal program."""

    def __init__(self, start, end, qbits, s_idx):
        self.start = start
        self.end = end
        self.s_idx = s_idx
        self.qbits = qbits

    def __repr__(self):
        s = (str(i) for i in self.start)
        e = (str(i) for i in self.end)
        return f"<Subexperiment:{self.s_idx}@ {':'.join(s)} to {':'.join(e)}>"


class _OutputParser(SubcircuitsVisitor):
    """(internal) Walks through the ouput, sorting into sub-experiments"""

    def __init__(self, scs, res, out):
        super().__init__(scs)
        self.res = res
        self.data = iter(out)
        for sc in self.subcircuits:
            sc._measurements = []

    def process_subcircuit(self):
        sc = self.subcircuits[self.s_idx]
        nxt = next(self.data)
        if isinstance(nxt, str):
            nxt = int(nxt[::-1], 2)
        sc._measurements.append(nxt)
        self.res._output.append((nxt, sc))


class ExecutionResult:
    """Captures the results of a Jaqal program's execution."""

    def __init__(self, circuit, output=None):
        """Encapsulates measurements made by Jaqal program.

        :param circuit: either a ScheduledCircuit representing a Jaqal program, or
            another ExecutionResult representing the desired Jaqal program
        :param output: (optional) A list of measurements to encapsulate

        """
        if isinstance(circuit, ExecutionResult):
            self._circuit = circuit._circuit
            self._expanded_circuit = circuit._expanded_circuit
            self._subexperiments = circuit._subexperiments
        else:
            self._circuit = circuit
            ec = self._expanded_circuit = expand_macros(fill_in_let(circuit))
            dc = DiscoverSubexperiments()
            self._subexperiments = tuple(
                Subexperiment(
                    sc.start,
                    sc.end,
                    sum(len(reg) for reg in ec.fundamental_registers()),
                    s_idx,
                )
                for s_idx, sc in enumerate(dc.visit(ec))
            )

        if output:
            self._parse_measurements(output)

    @property
    def subexperiments(self):
        """List of all prepare_all/measure_all sub-experiments.

        WARNING: The addresses are to a modified internal representation of the circuit.

        """
        return self._subexperiments

    def _parse_measurements(self, output, *, probabilities=None):
        """Parse the measurements an execution.

        :param output: a list of measurements, either bit strings, or integers
        :param probabilities: (boolean or None) whether to calculate the
            probabilities of outcomes (requires numpy).  No error is thrown if None.

        """
        if hasattr(self, "_output"):
            raise TypeError(
                "Cannot parse data: ExecutionResult already contains output data."
            )

        w = _OutputParser(self._subexperiments, self, output)
        self._output = []
        w.visit(self._expanded_circuit)

        if (probabilities is not None) and (not probabilities):
            return

        try:
            import numpy
        except ImportError as e:
            if probabilities:
                raise e
            else:
                return

        for sc in self._subexperiments:
            p = sc.probabilities = numpy.zeros(2 ** sc.qbits)
            for d in sc._measurements:
                p[d] += 1

            N = p.sum()
            p /= N

    @property
    def output_len(self):
        """The number of measurements made."""
        return len(self._output)

    def output(self, m_idx=None, *, fmt="str", s_idx=None):
        """Returns the output of the experiment.

        :param m_idx: Index of the measurement to show. None (default) shows all.
        :param fmt: How to format the output (see return, below)
        :param s_idx: Restrict to a sub-experiment (index). The default, None, collates
            from the whole circuit.

        :return: The measurement(s), with outcomes formatted as a:
            * 'int': little-endian integer
            * 'str': string containing 0s and 1s (default)

        """
        if s_idx is None:
            o = self._output
            if fmt == "int":
                if m_idx is None:
                    return [r for r, sc in o]
                else:
                    return o[m_idx][0]
            elif fmt == "str":
                if m_idx is None:
                    return [f"{r:b}".zfill(sc.qbits)[::-1] for r, sc in o]
                else:
                    r, sc = o[m_idx]
                    return f"{r:b}".zfill(sc.qbits)[::-1]
            else:
                raise TypeError(f"output() received unexpected fmt={fmt}.")
        else:
            sc = self._subexperiments[s_idx]
            o = sc._measurements
            if fmt == "int":
                if m_idx is None:
                    return o
                else:
                    return o[m_idx]
            elif fmt == "str":
                if m_idx is None:
                    return [f"{r:b}".zfill(sc.qbits)[::-1] for r in o]
                else:
                    r, sc = o[m_idx]
                    return f"{r:b}".zfill(sc.qbits)[::-1]
            else:
                raise TypeError(f"output() received unexpected fmt={fmt}.")

    def probabilities(self, s_idx, *, fmt="str"):
        """If available, returns the outcome probabilities for a given sub-experiment.

        :param s_idx: which prepare/measure block to return data for
        :param fmt: how to format the output (see return, below)

        :return: the probabilities as
            * 'int': a list, in order of outcomes, encoded as a little-endian integer
            * 'str': a dictionary, with strings containing 0s and 1s as keys (default)

        """
        sc = self._subexperiments[s_idx]
        p = sc.probabilities
        if fmt == "int":
            return p
        elif fmt == "str":
            return OrderedDict(
                [(f"{n:b}".zfill(sc.qbits)[::-1], v) for n, v in enumerate(p)]
            )

    def get_s_idx(self, m_idx):
        """Returns the index of the sub-experiments associated with a measurement.

        :param m_idx: an index of a measurement
        :return: the index of the sub-experiment that produced the measurement

        """

        return self._output[m_idx][1].s_idx


__all__ = ["ExecutionResult"]
