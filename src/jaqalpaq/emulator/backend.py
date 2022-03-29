# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import abc

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

    @abc.abstractmethod
    def execute(self):
        """Executes the job on the backend"""


class AbstractBackend:
    """Abstract Emulator Backend"""

    @abc.abstractmethod
    def __call__(self, circ):
        """Creates a job object for circ

        :param Circuit circ: circuit to run
        """

    def get_n_qubits(self, circ):
        """Returns the number of qubits the backend will simulate/emulate.

        Specifically, it will be the number of qubits in the considered circuit.

        :param circ: The circuit object being emulated/simulated.
        """

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

    def get_n_qubits(self, circ):
        """Returns the number of qubits the backend will be simulating.

        :param circ: The circuit object being emulated/simulated.
        """
        circuit_qubits = super().get_n_qubits(circ)
        if circuit_qubits > self.n_qubits:
            raise ValueError(f"{self} emulates fewer qubits than {circ} uses")
        return self.n_qubits

    def set_defaults(self, kwargs, **defaults):
        """Set parameters from a list of defaults and function kwargs.

        For every value passed as a keyword argument (into **defaults), set it in the
          object's namespace.  Values in kwargs overrided the default.  Values used from
          kwargs are removed from kwargs.

        :param kwargs: a dictionary of your function's keyword arguments, mutated to
          only contain unused values.
        """
        for k, v in defaults.items():
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
        """Return a dictionary of tuples of gate models and gate durations.

        This combs through the class's definition for all parameters named gate_*, and
          adds a corresponding entry in the returned dictionary, keyed by the associated
          gate name, of the gate model (i.e., the noisy process model) and the duration
          that the gate operates.
        : return dict: A dictionary of the models of the gates
        """
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
        mr = Readout(nxt, self.readout_index)
        subcircuit.accept_readout(mr)
        self.results.append(mr)
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
