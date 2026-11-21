import contextlib
import copy
import io
import os
import random
from pathlib import Path
from unittest.mock import patch

import matplotlib
matplotlib.use("Agg")

from core.bplus_tree import BplusTree
from core.config import BplusTreeConfig
from core.tree_printer import TreePrinter
from experiment.experiment_data import ExperimentDegrees, ExperimentRecords
from experiment.metrics import Metrics
from experiment.tree_experiment_runner import TreeExperimentRunner
from tui import Tui

# output of the program saved before refactoring, run with GOLDEN_RECORD=1 to save it again
GOLDEN_DIR = Path("tests/golden")
MODES = ["structure", "structure_collapse_rec", "leafs", "sequential"]


def check_golden(name: str, text: str):
    path = GOLDEN_DIR / f"{name}.txt"
    if os.environ.get("GOLDEN_RECORD"):
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f: f.write(text)
    with open(path, encoding="utf-8") as f:
        assert text == f.read()


def new_tree(name: str, debug: bool = False) -> BplusTree:
    conf = copy.deepcopy(BplusTreeConfig.PRESENTATION)
    conf.filepath = f"tests/table/golden_{name}"
    conf.override_file = True
    conf.debug = debug
    return BplusTree(conf)


def show_all(tree: BplusTree):
    for mode in MODES:
        # sequential mode crashes on free pages, the error is part of the saved output
        try: TreePrinter(tree).display(mode, mode)
        except RuntimeError as e: print(f"error: {e}")


def run_ops_file(filename: str, debug: bool = False) -> str:
    tree = new_tree(f"{filename}_{debug}", debug)
    tui = Tui(tree, None)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        with open(f"data/ops/{filename}") as f: tui.process_ops_file(f)
        show_all(tree)
    return out.getvalue()


def test_ops_files():
    for filename in ["min_h2.txt", "max_h2.txt", "min_h3.txt", "max_h3.txt"]:
        check_golden(f"ops_{filename[:-4]}", run_ops_file(filename))
    check_golden("ops_max_h3_debug", run_ops_file("max_h3.txt", debug=True))


def test_keyboard_ops():
    inputs = iter([
        "2", "8 3.1 1.2", "2", "3 1 1", "2", "20 7 7", "1", "8",
        "4", "8 12 5 5", "4", "3 3 9 9", "3", "20",
        "2", "1 2", "4", "8 1", "7", "9",
    ])

    def fake_input(prompt: str = "") -> str:
        print(prompt, end="")
        return next(inputs)

    tree = new_tree("keyboard")
    tui = Tui(tree, None)
    out = io.StringIO()
    with patch("builtins.input", fake_input), contextlib.redirect_stdout(out):
        tui.menu_keyboard_ops()
    check_golden("keyboard_ops", out.getvalue())


@patch("experiment.tree_experiment_runner.TreeExperimentRunner.TEMP_PATH_STR", "./tests/experiment/table/temp")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.MAIN_PATH_STR", "./tests/experiment/table/main")
def test_experiments():
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        random.seed(7)
        conf = BplusTreeConfig(filepath=TreeExperimentRunner.MAIN_PATH_STR, override_file=True)
        runner = TreeExperimentRunner(BplusTree(conf), Metrics())
        runner.show_chart_and_table = False

        runner.run_experiment(ExperimentDegrees(
            name="golden", operation_amount=20, rec_amount=200, data=[(2, 2), (4, 4), (2, 4)]))
        print(runner._results)

        runner.run_experiment(ExperimentRecords(
            name="golden", operation_amount=20, leaf_degree=2, node_degree=3, data=[100, 300, 200]))
        print(runner._results)
    check_golden("experiments", out.getvalue())
