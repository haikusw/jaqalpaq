# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.

import argparse
from .qsyntax import is_qcircuit
from jaqalpaq.generator import generate_jaqal_program


def main():
    args = get_args()
    try:
        ns = run_in_namespace(args.filename)
        target = choose_target(ns, target=args.target)
        jaqal = create_jaqal_code(target)
        write_jaqal_code(args.out, jaqal)
    except Exception as exc:
        print(f"ERROR: {exc}")


def get_args():
    parser = argparse.ArgumentParser(
        description="Compile a high-level Jaqal file in Q syntax to Jaqal assembly code"
    )

    parser.add_argument(
        "filename",
        nargs="+",
        help="The name of the files to compile. Files specified later may reference objects created in earlier files.",
    )
    parser.add_argument(
        "-o",
        "--out",
        help="The name of the output Jaqal file. If omitted write to the screen.",
    )
    parser.add_argument(
        "-t",
        "--target",
        help="The name of the circuit in the file to run, if more than one are valid targets",
    )

    return parser.parse_args()


def run_in_namespace(filenames):
    """Run the given files as Python files and return the global namespace
    when all are done executing."""
    ns = {}
    for filename in filenames:
        with open(filename, "r") as fd:
            exec(fd.read(), ns)
    return ns


def choose_target(ns, target=None):
    """Choose the target function from the namespace. First we go by what
    the user specified, if anything, and make sure it is valid. Then we
    see if there is exactly one valid target, and return it."""
    valid_targets = find_valid_targets(ns)
    if target is not None:
        if target in valid_targets:
            return valid_targets[target]
        elif target in ns:
            raise ValueError(
                f"Target `{target}' exists but is not a valid target. A valid target must be decorated with Q.circuit and take no arguments."
            )
        else:
            raise ValueError(f"Target `{target}' not found")

    if len(valid_targets) == 1:
        key = list(valid_targets.keys())[0]
        return valid_targets[key]
    else:
        if len(valid_targets) == 0:
            raise ValueError(
                "No valid targets found. A valid target must be decorated with @circuit and take Q as its only argument."
            )
        else:
            raise ValueError(
                f"Too many valid targets found: `{', '.join(valid_targets.keys())}'. Use -t to specify which one."
            )


def find_valid_targets(ns):
    """Return all functions in namespace that take zero arguments and have
    the QCIRCUIT_FUNCTION attribute."""

    return {name: value for name, value in ns.items() if is_valid_target(value)}


def is_valid_target(obj):
    return is_qcircuit(obj, argcount=0)


def create_jaqal_code(target):
    """Create a Jaqal string from the given target function."""
    return generate_jaqal_program(target())


def write_jaqal_code(out, jaqal):
    """Write the jaqal code to the given file if provided, or the screen
    otherwise."""
    if out is not None:
        with open(out, "w") as fd:
            fd.write(jaqal)
    else:
        print(jaqal)


if __name__ == "__main__":
    main()
