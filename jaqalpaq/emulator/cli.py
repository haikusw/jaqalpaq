import sys, argparse
from jaqalpaq.parser import parse_jaqal_string


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        prog="jaqal", description="Execute a Jaqal program via noiseless emulator"
    )
    parser.add_argument(
        "filename",
        default=None,
        nargs="?",
        help="Jaqal file to execute (default to reading from stdin)",
    )
    parser.add_argument(
        "--suppress-output",
        "-s",
        dest="suppress",
        action="store_true",
        help="Do not produce literal Jaqal output, i.e., a time-ordered list of bit strings.  Implies -p, and outputs to stdout.",
    )
    parser.add_argument(
        "--probabilities",
        "-p",
        dest="probs",
        metavar="FORMAT",
        default=None,
        nargs="?",
        const="str",
        help="Print distribution probabilities of outcomes to stderr.  Listed in lexical order.  Takes optional argument FORMAT `str` to print bitstrings, and `int` to print probabilities in integer order of outcomes, little-endian encoded. If set, defaults to `str`.",
    )
    parser.add_argument(
        "--cutoff",
        dest="cutoff",
        default=1e-12,
        help="Do not display probabilties less than CUTOFF.  Defaults to 1e-12.  Ignored if FORMAT is `int`",
    )
    parser.add_argument(
        "--output",
        dest="output",
        default=None,
        choices=["human", "python", "json", "validation"],
        nargs=1,
        help="Determines if `human` readible probability, `python` dictionary, or `json` output.  [undocumented] validation template",
    )
    parser.add_argument(
        "--validate",
        dest="validate",
        action="store_true",
        help="[undocumented] Performs a validation of jaqal versus the expressed expected results.",
    )
    parser.add_argument(
        "--debug-traces",
        "-d",
        dest="debug",
        action="store_true",
        help="Automatically invoke the post-mortem debugger on exception",
    )

    ns = parser.parse_args(argv)
    try:
        ns.cutoff = float(ns.cutoff)
    except Exception:
        print(f"Invalid cutoff {ns.cutoff}", file=sys.stderr)
        return 2

    if not ns.output:
        ns.output = "human"
    else:
        (ns.output,) = ns.output

    if ns.filename:
        with open(ns.filename, "r") as f:
            txt = f.read()
    else:
        txt = sys.stdin.read()

    from .noiseless import run_jaqal_file, run_jaqal_circuit
    from ._validator import validate_jaqal_string, generate_jaqal_validation
    from jaqalpaq.parser import parse_jaqal_string
    from jaqalpaq.core.result import ExecutionResult

    if ns.validate:
        try:
            v = validate_jaqal_string(txt)
        except Exception as ex:
            if ns.debug:
                import pdb, traceback

                traceback.print_exc()
                _, _, tb = sys.exc_info()
                pdb.post_mortem(tb)
                return 1
            else:
                print(f"Validation failure: {type(ex).__name__}: {ex}")
                return 1

        if v:
            a = '", "'
            print(f'Validations: "{a.join(v)}" passed.')
        else:
            print("Warning: no validation data present")
        return

    try:
        circ = parse_jaqal_string(txt, autoload_pulses=True)
    except Exception as ex:
        if ns.debug:
            import pdb, traceback

            traceback.print_exc()
            _, _, tb = sys.exc_info()
            pdb.post_mortem(tb)
            return 1
        else:
            print(f"Error during parsing: {type(ex).__name__}: {ex}")
            return 1

    if not ns.suppress:
        exe = run_jaqal_circuit(circ)
        if ns.output != "validation":
            print("\n".join(exe.output(fmt="str")), flush=True)
        out = sys.stderr
    else:
        exe = ExecutionResult(circ)
        out = sys.stdout

    if ns.output == "validation":
        print(generate_jaqal_validation(exe))
        return

    if ns.suppress or ns.probs or ns.output:
        if not ns.probs:
            ns.probs = "str"

        probs = []
        for n in range(len(exe.subexperiments)):
            prob = exe.probabilities(n, fmt=ns.probs)
            if ns.probs == "int":
                probs.append(list(prob))
            elif ns.cutoff > 0:
                prob = dict([(k, v) for k, v in prob.items() if v >= ns.cutoff])
                probs.append(prob)

        if ns.output == "json":
            # This should be identical to python for our use case.
            import json

            print(json.dumps(probs), file=out)
        elif ns.output == "python":
            print(repr(probs), file=out)
        elif ns.output == "human":
            for n, prob in enumerate(probs):
                print(f"Sub-experiment {n}:", file=out)
                if ns.probs == "int":
                    print("\n".join(f"{o}: {p}" for o, p in enumerate(prob)), file=out)
                else:
                    print("\n".join(f"{o}: {p}" for o, p in prob.items()), file=out)
        else:
            assert False
