(
    "circuit",
    ("let", "pi", 3.14159265359),
    ("let", "pi2", 1.57079632679),
    ("let", "pi4", 0.78539816339),
    ("let", "mpi2", -1.57079632679),
    ("register", "q", 2),
    (
        "macro",
        "hadamard",
        "target",
        (
            "sequential_block",
            ("gate", "R", "target", "pi2", "pi2"),
            ("gate", "R", "target", 0, "pi"),
        ),
    ),
    (
        "macro",
        "cnot",
        "control",
        "target",
        (
            "sequential_block",
            ("gate", "R", "control", "pi2", "pi2"),
            ("gate", "MS", "control", "target", 0, "pi4"),
            (
                "parallel_block",
                ("gate", "R", "control", 0, "mpi2"),
                ("gate", "R", "target", 0, "mpi2"),
            ),
            ("gate", "R", "control", "pi2", "pi2"),
        ),
    ),
    ("gate", "prepare_all"),
    ("gate", "hadamard", ("array_item", "q", 0)),
    ("gate", "cnot", ("array_item", "q", 1), ("array_item", "q", 0)),
    ("gate", "measure_all"),
)
