JaqalPaq
--------

JaqalPaq is a python package used to parse, manipulate, emulate, and generate
quantum assembly code written in [Jaqal](https://qscout.sandia.gov/jaqal)
(Just another quantum assembly language).  JaqalPaq can be installed with
optional transpilers that convert code written in other quantum assembly
languages to a version of Jaqal whose native gates are relevant for
[QSCOUT](https://qscout.sandia.gov/) (Quantum Scientific Computing Open User
Testbed).

## Code

JaqalPaq is available on [GitLab](https://gitlab.com/jaqal/jaqalpaq) under
the Apache 2.0 License.

## Installation

> **TLDR**: Inside a venv/conda env:
>
> ```bash
> pip install --upgrade Cython numpy pip wheel
> pip install ipykernel JaqalPaq'[pygsti-integration]' QSCOUT-gatemodels
> ipython kernel install --name=jaqal --user
> ```

### Step 0: Prepare base dependencies

JaqalPaq requires Python 3.6 (or later), but Python 3.7 (or later) is
recommended.  To check your installed version, run

```bash
python3 --version
```

Windows users are encouraged to install under WSL2.  You may also consider
[conda](https://conda.io), which provides a platform-independent Python
installation.

We also recommend having a functional C compiler and Python headers installed.
Depending on your Python version and platform, this may be entirely
unneccessary.  You can confirm the presence of these headers by running

```bash
python3-config --includes
```

When properly configured, this will output a list of include directives that
will be passed to your compiler, e.g.,

```
-I/usr/include/python3.6m
```

On apt-based systems, these dependencies can be installed by running (as root)

```bash
apt install python3-dev build-essential
```

On rpm-based ones,

```bash
yum install python3-devel gcc gcc-c++
```

Mac users may need to install XCode to ensure they have a functional C++
compiler.  Similarly Windows users may need to install VS build tools.

Conda users should have these header files and compilers installed
automatically.

### Step 1: (recommended) Prepare a virtual environment

> **WARNING**: JaqalPaq's dependencies may sometimes conflict with each other.
> Upgrading may introduce incompatible versions, and for this reason we
> STRONGLY recommend installing within some kind of virtual environment.

To create a Python virtual environment, run

```bash
python3 -m venv /path/to/venv
```

The location of the venv is left to your discretion, but please be aware that
a full installation will be ~100s of megabytes.

To create a conda virtual environment, run

```bash
conda create --name your-preferred-name python=3.9
```

To enter the virtual environment, run

```bash
source /path/to/venv/bin/activate
```

or

```bash
conda activate your-preferred-name
```

respectively.

> **NOTE**: All following steps should be performed inside the virtual
> environment.  If you close your terminal, you will have to enter the virtual
> environment again, using the appropriate command above.

If you are using a venv, upgrade pip and install wheel:

```bash
pip install --upgrade pip wheel
```

[Jupyter](https://jupyter.org/) users can install a kernel to access this
virtual environment by running

```bash
pip install ipykernel
ipython kernel install --name=preferred-name --user
```

> **NOTE**: Restart the Jupyter server.  A new kernel will be available.

If you no longer want that kernel, you can remove it with

```bash
jupyter kernelspec remove pip-jaqal
```

> **NOTE**: Unlike every other command, this must be performed from the
> environment in which Jupyter is installed, and NOT the JaqalPaq environment.

### Step 2: Install JaqalPaq and friends

JaqalPaq packages are provided with [pip](https://pip.pypa.io/en/stable/).

> **WARNING**: Some dependencies may conflict with each other.  Be sure to
> include all desired dependencies on this line.  It is safe to re-run the
> whole command with a new desired feature set.

```bash
pip install JaqalPaq'[pygsti-integration,notebooks]' QSCOUT-gatemodels \
    JaqalPaq-extras'[qiskit,pyquil,cirq,projectq,pytket,tutorial]'
```

 - `pygsti-integration` provides the emulator.
 - `notebooks` installs all dependencies for the chemistry example notebook
 - `QSCOUT-gatemodels` provides the native gates of the
   [QSCOUT](https://qscout.sandia.gov/) project , which are modeled as
   pure-state  preparations, unitary transformations, and destructive
   measurements. See
   [QSCOUT-gatemodels](https://pypi.org/project/QSCOUT-gatemodels/) for
   details.
 - The five transpiler targets for JaqalPaq-extras each install a compatible
   version of the respective third-party package.
 - `tutorial` installs an additional dependency required for the
   JaqalPaq-extras tutorial notebook to run.

> **NOTE**: The `notebooks`, `qiskit`, `pyquil`, `cirq`, `projectq`, `pytket`,
> and `tutorial` targets will install a large number of third-party packages.
> You should consider only installing the subset of these packages that you
> plan on using.

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

## Testing and examples

Underneath your environment prefix, navigate to `share/jaqalpaq`.  Inside a
venv, run

```bash
cd "$VIRTUAL_ENV/share/jaqalpaq"
```

or, inside a conda environment,

```bash
cd "$CONDA_PREFIX/share/jaqalpaq"
```

Example Jaqal files, as well as tutorials and example quantum chemistry
calculations are in the `examples/` directory.  To run the tests, first
install pytest,

```bash
pip install pytest
```

and then run it on the `tests/` directory:

```bash
pytest tests
```

## Documentation

Online documentation is hosted on [Read the Docs](https://jaqalpaq.readthedocs.io).


## License
[Apache 2.0](https://choosealicense.com/licenses/apache-2.0/)

## Questions?

For help and support, please contact [qscout@sandia.gov](mailto:qscout@sandia.gov).
