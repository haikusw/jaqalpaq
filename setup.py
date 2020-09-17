"""Python tools for Jaqal"""

from setuptools import setup, find_packages

name = "JaqalPaq"
description = "Python tools for Jaqal"
version = "1.0.0rc1"

setup(
    name=name,
    description=description,
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    version=version,
    author="Benjamin C. A. Morrison, Jay Wesley Van Der Wall, Daniel Lobser, Antonio Russo, Kenneth Rudinger, Peter Maunz",
    author_email="qscout@sandia.gov",
    packages=find_packages(include=["jaqalpaq", "jaqalpaq.*"], where="src"),
    package_dir={"": "src"},
    package_data={"jaqalpaq.parser": ["jaqal_grammar.lark"]},
    install_requires=["lark-parser"],
    extras_require={
        "tests": ["pytest"],
        "docs": [
            "sphinx",
            "sphinx-rtd-theme",
            f"jaqalpaq-extras[qiskit,pyquil,cirq,projectq,pytket]=={version}",
        ],
        "pygsti-integration": ["pygsti"],
    },
    python_requires=">=3.6.5",
    platforms=["any"],
    url="https://qscout.sandia.gov",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Physics",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Unix",
    ],
    entry_points={"console_scripts": ["jaqal-emulate = jaqalpaq._cli:main"]},
)
