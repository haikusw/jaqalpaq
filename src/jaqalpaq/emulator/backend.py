# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from numpy.random import choice

from jaqalpaq.core.result import ExecutionResult, Readout
from jaqalpaq.core.result import ProbabilisticSubcircuit
from jaqalpaq.core.algorithm.walkers import TraceVisitor, DiscoverSubcircuits


class AbstractJob:
    """Abstract Jaqal Compute Job"""

    def __init__(self, backend, circuit):
        self.backend = backend
        self.circuit = circuit

    def __repr__(self):
        return f"<{type(self)} of {self.backend}>"

    def execute(self):
        """Executes the job on the backend"""
        raise NotImplementedError()


class AbstractBackend:
    """Abstract Emulator Backend"""

    def __call__(self, circ):
        """Creates a job object for circ

        :param Circuit circ: circuit to run
        """
        raise NotImplementedError()

    def get_n_qubits(self, circ=None):
        """Returns the number of qubits the backend will simulate/emulate.

        Specifically, it will be the number of qubits in the considered circuit.

        :param circ: The circuit object being emulated/simulated.
        """

        if circ is None:
            raise ValueError(
                f"A circuit must be passed to {type(self).__name__}.get_n_qubits"
            )

        registers = circ.fundamental_registers()

        try:
            (register,) = registers
        except ValueError:
            raise NotImplementedError("Multiple fundamental registers unsupported.")

        return register.size


class ExtensibleBackend(AbstractBackend):
    """Abstract mixin providing an interface for extending a backend.

    Every gate to be emulated should have a corresponding gate_{name} and
      gateduration_{name} method defined.
    """

    def __init__(self, n_qubits, stretched_gates=None, **kwargs):
        """(abstract) Perform part of the construction of a noisy model.

        :param n_qubits: The number of qubits to simulate
        :param stretched_gates: (default False)  Add stretched gates to the model:
          - If None, do not modify the gates.
          - If 'add', add gates with '_stretched' appended that take an extra parameter,
            a stretch factor.
          - Otherwise, stretched_gates must be the numerical stretch factor that is
            applied to all gates (no extra stretched gates are added
        """
        self.n_qubits = n_qubits
        self.stretched_gates = stretched_gates
        model, durations = self.build_model()
        super().__init__(model=model, gate_durations=durations, **kwargs)

    def get_n_qubits(self, circ=None):
        """Returns the number of qubits the backend will be simulating.

        :param circ: The circuit object being emulated/simulated.
        """
        return self.n_qubits

    def set_defaults(self, kwargs, **values):
        """Helper function to set default values.
        For every value passed as a keyword argument or in kwargs, set it in the object's
          namespace, with values in kwargs taking precedence.

        :param kwargs: a dictionary of your function's keyword arguments
        """
        for k, v in values.items():
            setattr(self, k, kwargs.pop(k, v))

    @staticmethod
    def _curry(params, *ops):
        """Helper function to make defining related gates easier.
        Curry every function in ops, using the signature description in params.  For
          every non-None entry of params, pass that value to the function.

        :param params: List of parameters to pass to each op in ops, with None allowing
          passthrough of values in the new function
        :param ops: List of functions to curry
        :return List[functions]: A list of curried functions
        """

        def _inner(op):
            def newop(self, *args, **kwargs):
                args = iter(args)
                argv = [next(args) if param is None else param for param in params]
                argv.extend(args)
                return op(self, *argv, **kwargs)

            return newop

        newops = []
        for op in ops:
            newops.append(_inner(op))

        return newops

    def collect_gate_models(self):
        gate_models = {}

        for gate_name in type(self).__dict__:
            if not gate_name.startswith("gate_"):
                continue

            name = gate_name[5:]
            gate_models[name] = (
                getattr(self, gate_name),
                getattr(self, f"gateduration_{name}"),
            )

        return gate_models


class IndependentSubcircuitsEmulatorWalker(TraceVisitor):
    def __init__(self, traces, subcircuits):
        """(internal) Instantiates an EmulationWalker.

        Produce emulated output sampled from a given probability distribution.

        :param List[Trace] traces: the prepare_all/measure_all subcircuits
        :param List[List[Float]] probabilities: the probabilities of each outcome

        """
        super().__init__(traces)
        self.results = []
        self.readout_index = 0
        self.subcircuits = subcircuits
        # This is only valid because we must always do measure_all.
        if self.traces:
            self.qubits = len(self.traces[0].used_qubits)

    def process_trace(self):
        subcircuit = self.subcircuits[self.index]
        nxt = choice(2**self.qubits, p=subcircuit.probability_by_int)
        mr = Readout(nxt, self.readout_index, subcircuit)
        self.results.append(mr)
        subcircuit._readouts.append(mr)
        self.readout_index += 1


class IndependentSubcircuitsJob(AbstractJob):
    """Job for circuit with subcircuits that are independent"""

    def execute(self):
        w = IndependentSubcircuitsEmulatorWalker(self.traces, self.subcircuits)
        w.visit(self.circuit)
        return ExecutionResult(self.subcircuits, w.results)


class IndependentSubcircuitsBackend(AbstractBackend):
    """Abstract emulator backend for subcircuits that are independent"""

    def __call__(self, circ):
        """Attaches the backend to a particular circuit, creating a Job object.

        Calculates the probabilities of outcomes for every subcircuit.

        :param Circuit circ: parent circuit

        :returns IndependentSubcircuitsJob:
        """

        job = IndependentSubcircuitsJob(self, circ)
        visitor = DiscoverSubcircuits()
        job.traces = traces = visitor.visit(circ)
        job.subcircuits = [self._make_subcircuit(job, *tr) for tr in enumerate(traces)]

        return job
