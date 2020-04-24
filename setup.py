"""Python tools for Jaqal"""

import sys
from setuptools import setup
try:
    from sphinx.setup_command import BuildDoc
except ImportError:
    print("Warning: document cannot be built without sphinx")
    BuildDoc = None

name = "Jaqal-pup"
description = "Python tools for Jaqal"
version = "1.0"

setup(
    name=name,
    description=description,
    version=version,
    author="Benjamin C. A. Morrison, Jay Wesley Van Der Wall, Lobser, Daniel, Antonio Russo, Kenneth Rudinger, Peter Maunz",
    author_email="qscout@sandia.gov",
    packages=[
        "jaqal",
        "jaqal.core",
        "jaqal.generator",
        "jaqal.parser",
        "jaqal.pygsti",
    ],
    package_dir={"": "."},
    install_requires=["lark-parser"],
    extras_require={"tests": ["pytest"], "docs": ["sphinx"], "pygsti-integration": ["pygsti"]},
    python_requires=">=3.7",
    platforms=["any"],
    url="https://qscout.sandia.gov",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: Physics",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Unix",
    ],
    cmdclass={"build_sphinx": BuildDoc},
)
