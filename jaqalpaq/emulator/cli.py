import sys, argparse


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
        default=False,
        const=True,
        action="store_const",
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
        help="""Print distribution probabilities of outcomes to stderr.  Listed in lexical order.  Takes optional argument FORMAT `str` to print bitstrings, and `int` to print probabilities in integer order of outcomes, little-endian encoded. If set, defaults to `str`.""",
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
        nargs=1,
        help="Determines if `human` readible probability, `python` dictionary, or `json` output.",
    )

    ns = parser.parse_args(argv)
    try:
        ns.cutoff = float(ns.cutoff)
    except Exception:
        print(f"Invalid cutoff {ns.cutoff}", file=sys.stderr)
        return 1

    from .noiseless import run_jaqal_file, run_jaqal_string

    if ns.filename:
        exe = run_jaqal_file(ns.filename)
    else:
        exe = run_jaqal_string(sys.stdin.read())

    if not ns.output:
        ns.output = "human"
    else:
        (ns.output,) = ns.output
        ns.suppress = True

    if not ns.suppress:
        print("\n".join(exe.output(fmt="str")))

    if ns.suppress:
        out = sys.stdout
    else:
        out = sys.stderr

    if ns.suppress or ns.probs or ns.output:
        if not ns.probs:
            ns.probs = "str"

        if ns.output == "validation":
            print("// EXPECTED MEASUREMENTS")
            print(
                "\n".join(
                    " ".join(
                        (
                            "//",
                            exe.output(n),
                            str(exe.output(n, fmt="int")),
                            str(exe.get_s_idx(n)),
                        )
                    )
                    for n in range(exe.output_len)
                )
            )

            print("\n// EXPECTED PROBABILITIES")

            for s_idx, se in enumerate(exe.subexperiments):
                print(f"// SUBEXPERIMENT {s_idx}")
                for (n, ((s, ps), p)) in enumerate(
                    zip(
                        exe.probabilities(s_idx).items(),
                        exe.probabilities(s_idx, fmt="int"),
                    )
                ):
                    assert ps == p
                    print(f"// {s} {n} {p}")

            return 0

        probs = []
        for n in range(len(exe.subexperiments)):
            probs.append(exe.probabilities(n, fmt=ns.probs))
            if ns.probs == "int":
                continue

            if ns.cutoff > 0:
                probs[-1] = dict(
                    [(k, v) for k, v in probs[-1].items() if v >= ns.cutoff]
                )

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
                    print("\n".join(f"{o}: {p}" for o, p in enumerate(prob)))
                else:
                    print("\n".join(f"{o}: {p}" for o, p in prob.items()))
        else:
            print(f"Unknown output format {ns.output}.", file=sys.stderr)
            return 1
