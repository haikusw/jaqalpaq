JaqalPaq
--------

# JaqalPaq

JaqalPaq is a python package used to parse, manipulate, emulate, and generate
quantum assembly code written in [Jaqal](https://qscout.sandia.gov/jaqal)
(Just another quantum assembly language).  JaqalPaq can be installed with
optional transpilers that convert code written in other quantum assembly
languages to a version of Jaqal whose native gates are relevant for
[QSCOUT](https://qscout.sandia.gov/) (Quantum Scientific Computing Open User
Testbed).

## Installation

JaqalPaq is available on [GitLab](https://gitlab.com/jaqal/jaqalpaq).  Use the
package manager [pip](https://pip.pypa.io/en/stable/) to install it.

```bash
pip install jaqalpaq
```

To install the optional transpiler suite, use the following:

```bash
pip install jaqalpaq-extras
```

The JaqalPaq emulator can be programmed to emulate any native gate set.
However, we only currently provide an emulator for
[QSCOUT](https://qscout.sandia.gov/) native operations, which are modeled as
pure-state preparations, unitary transformations, and destructive
measurements.  This is available on Gitlab in the
[QSCOUT Gate Models](https://gitlab.com/jaqal/qscout-gatemodels)
repository.  [pyGSTi](https://www.pygsti.info/) is used to perform forward
simulations.  To install this capability, use the following

```bash
pip install qscout-gatemodels pygsti
```

## Usage

The following simple example is from `examples/usage_example.py`


```python
import jaqalpaq
from jaqalpaq.parser import parse_jaqal_file
from jaqalpaq.emulator import run_jaqal_circuit
from jaqalpaq.generator import generate_jaqal_program

JaqalCircuitObject = parse_jaqal_file("jaqal/Sxx_circuit.jaqal")
JaqalCircuitResults = run_jaqal_circuit(JaqalCircuitObject)
print(f"Probabilities: {JaqalCircuitResults.subcircuits[0].probability_by_str}")
JaqalProgram = generate_jaqal_program(JaqalCircuitObject)
```

The Jaqal file processed by this example, `examples/jaqal/Sxx_circuit.jaqal`, is

```python
from qscout.v1.std usepulses *

register q[2]

prepare_all
Sxx q[1] q[0]
measure_all
```

More extensive examples, including detailed Jupyter notebooks implementing the
variational quantum eigensolver (VQE) quantum algorithm for some simple
molecules, can be found in the `examples` directory.

For information on the JaqalPaq emulator's command-line interface, run the
following in your shell:

```bash
jaqal-emulate --help
```

## Documentation

Online documentation is hosted on [Read the Docs](https://jaqalpaq.readthedocs.io).


## License
[Apache 2.0](https://choosealicense.com/licenses/apache-2.0/)

## Questions?

For help and support, please contact [qscout@sandia.gov](mailto:qscout@sandia.gov).
