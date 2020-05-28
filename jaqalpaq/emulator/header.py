import sys
from importlib import import_module


def collect_native_gates(usepulses):
    ng = {}
    for name, filt in usepulses.items():
        name = str(name)
        mod = import_module(name)
        modng = mod.NATIVE_GATES
        assert filt is all
        for g in mod.NATIVE_GATES:
            ng[g.name] = g

    return ng
