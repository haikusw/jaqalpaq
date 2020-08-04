# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from collections import OrderedDict

import numpy as np

from jaqalpaq import JaqalError
from jaqalpaq.parser import JaqalParseError

from .noiseless import run_jaqal_string


def assertAlmostEqual(a, b):
    if np.isclose(a, b):
        return

    raise ValueError(f"{a} and {b} differ by {a-b}")


def assertEqual(a, b):
    if a == b:
        return

    raise ValueError(f"{a} != {b}")


def assertisinstance(a, b):
    if isinstance(a, b):
        return

    raise TypeError(f"{type(a)} is not an instance of {b}")


def generate_jaqal_validation(exe):
    """[undocumented] Generate a description of the execution of a circuit

    :param exe: the ExecutionResult object to describe
    :return: a string that can appended to a Jaqal program and validated

    """
    output = []
    emit = output.append

    emit("// EXPECTED READOUTS")
    emit(
        "\n".join(
            " ".join(("//", mr.as_str, str(mr.as_int), str(mr.subcircuit.index),))
            for mr in exe.readouts
        )
    )

    emit("\n// EXPECTED PROBABILITIES")

    for sc_index, se in enumerate(exe.subcircuits):
        emit(f"// SUBCIRCUIT {sc_index}")
        for (n, ((s, ps), p)) in enumerate(
            zip(se.probability_by_str.items(), se.probability_by_int)
        ):
            assert ps == p
            emit(f"// {s} {n} {p}")

    return "\n".join(output)


def parse_jaqal_validation(txt):
    """[undocumented] parse Jaqal validation comments

    :param txt: a full Jaqal program, possibly with validation comments
    :return: a dictionary describing the validation

    """
    section = None
    expected = {}
    s_idx = -1

    for line in txt.split("\n"):
        line = line.strip()

        # Resest on non-comments
        if not line.startswith("//"):
            section = None
            s_idx = -1
            continue

        line = line[2:].strip()

        # Resest on empty comments
        if len(line) == 0:
            section = None
            s_idx = -1
            continue

        if section == "meas":
            true_str, true_int, subcirc = line.split()
            true_str_list.append(true_str)
            true_int_list.append(int(true_int))
            subcirc_list.append(int(subcirc))
        elif section == "prob":
            if line.startswith("SUBCIRCUIT "):
                s_idx_n = int(line[11:].strip())
                if s_idx_n != s_idx + 1:
                    raise ValueError("Malformed validation.")

                s_idx = s_idx_n

                str_prob[s_idx] = OrderedDict()
                int_prob[s_idx] = OrderedDict()
                continue

            key_str, key_int, val = line.split()
            val = float(val)
            str_prob[s_idx][key_str] = val
            int_prob[s_idx][int(key_int)] = val
        elif section == "error":
            exc_name, *exc_message = line.split(": ", 1)
            if exc_name == "jaqalpaq.error.JaqalError":
                exc = JaqalError
            elif exc_name == "jaqalpaq.parser.tree.JaqalParseError":
                exc = JaqalParseError
            else:
                raise NotImplementedError(f"Unwhitelisted exception {exc_name}")
            expected["error"] = exc, exc_message
        else:
            if section is not None:
                raise ValueError("Malformed validation.")

            if line == "EXPECTED READOUTS":
                section = "meas"
                true_str_list = expected["true_str_list"] = []
                true_int_list = expected["true_int_list"] = []
                subcirc_list = expected["subcirc_list"] = []
            elif line == "EXPECTED PROBABILITIES":
                section = "prob"
                str_prob = expected["str_prob"] = {}
                int_prob = expected["int_prob"] = {}
            elif line == "EXPECTED ERROR":
                section = "error"

    return expected


def validate_jaqal_string(txt):
    """[undocumented] validate a Jaqal program with validation comments

    :param txt: a full Jaqal program, possibly with validation comments
    :return: a list of validations performed

    """
    expected = parse_jaqal_validation(txt)

    if "error" in expected:
        exc, exc_message = expected["error"]
        try:
            exe = run_jaqal_string(txt)
        except Exception as e:
            assertisinstance(e, exc)
            if len(exc_message) > 0:
                assertEqual(exc_message[0], str(e))
        else:
            raise ValueError("Expected an exception, but none thrown.")
        return ["raised expected exception"]

    exe = run_jaqal_string(txt)

    validated = []
    if "true_str_list" in expected:
        true_str_list = expected["true_str_list"]
        true_int_list = expected["true_int_list"]
        subcirc_list = expected["subcirc_list"]

        assertEqual(true_str_list, [a.as_str for a in exe.readouts])
        assertEqual(true_int_list, [a.as_int for a in exe.readouts])

        for n, t_str in enumerate(true_str_list):
            assertEqual(t_str, exe.readouts[n].as_str)
            assertEqual(true_int_list[n], exe.readouts[n].as_int)
            assertEqual(subcirc_list[n], exe.readouts[n].subcircuit.index)
        validated.append("measurements agree")

    if "str_prob" in expected:
        str_prob = expected["str_prob"]
        for n, act_P in enumerate(exe.subcircuits):
            exp_P = str_prob[n]
            for (ka, va), (kb, vb) in zip(
                exp_P.items(), act_P.probability_by_str.items()
            ):
                assertEqual(ka, kb)
                assertAlmostEqual(va, vb)

        int_prob = expected["int_prob"]
        for n, act_P in enumerate(exe.subcircuits):
            exp_P = int_prob[n]
            for (ka, va), (kb, vb) in zip(
                exp_P.items(), enumerate(act_P.probability_by_int),
            ):
                assertEqual(ka, kb)
                assertAlmostEqual(va, vb)

        validated.append("probabilities agree")

    return validated
