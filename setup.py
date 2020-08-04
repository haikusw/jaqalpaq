"""Python tools for Jaqal"""

import sys
from setuptools import setup, find_packages
import os, shutil
from os.path import dirname, join

# copytree with dirs_exist_ok is too new
def copytree(src, dst, dirs_exist_ok=True):
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)

    for sdir, dirnames, files in os.walk(src):
        ddir = sdir.replace(src, dst, 1)
        if not os.path.exists(ddir):
            os.makedirs(ddir)
        for f in files:
            sfile = os.path.join(sdir, f)
            dfile = os.path.join(ddir, f)
            if os.path.exists(dfile):
                if not dirs_exist_ok:
                    raise RuntimeError("unsupported feature")
                if os.path.samefile(sfile, dfile):
                    continue
                os.remove(dfile)
            shutil.copy(sfile, ddir)


try:
    from sphinx.setup_command import BuildDoc
except ImportError:
    print("Warning: document cannot be built without sphinx")
    DoBuildDoc = None
else:

    try:
        import jaqalpaq.transpilers as jet
    except ImportError:
        DoBuildDoc = BuildDoc
    else:
        extra_doc = join(dirname(dirname(dirname(jet.__file__))), "doc")

        class DoBuildDoc(BuildDoc):
            def _guess_source_dir(self):
                root = super()._guess_source_dir()
                copytree(extra_doc, root, dirs_exist_ok=True)
                return root


name = "JaqalPaq"
description = "Python tools for Jaqal"
version = "1.0.0b1"

setup(
    name=name,
    description=description,
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    version=version,
    author="Benjamin C. A. Morrison, Jay Wesley Van Der Wall, Daniel Lobser, Antonio Russo, Kenneth Rudinger, Peter Maunz",
    author_email="qscout@sandia.gov",
    packages=find_packages(include=["jaqalpaq", "jaqalpaq.*"]),
    package_dir={"": "."},
    package_data={"jaqalpaq.parser": ["jaqal_grammar.lark"],},
    install_requires=["lark-parser"],
    extras_require={
        "tests": ["pytest"],
        "docs": ["sphinx", "sphinx-rtd-theme"],
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
    cmdclass={"build_sphinx": DoBuildDoc},
    entry_points={"console_scripts": ["jaqal-emulate = jaqalpaq._cli:main"],},
)
