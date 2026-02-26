import copy
import math
import random
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Tuple, List, ClassVar, Literal
import matplotlib.pyplot as plt
import pandas as pd


from core.bplus_tree import BplusTree
from core.config import BplusTreeConfig
from core.structures.record import Record
from experiment.metrics import Metrics
from experiment.experiment_data import ExperimentDegrees, ExperimentRecords

@dataclass()
class ExperimentOperationResult:
    theo_bc_o: float = 0
    theo_wc_o: float = 0
    mean_o: float = 0

    theo_bc_i: float = 0
    theo_wc_i: float = 0
    mean_i: float = 0
    def reset(self):
        self.theo_bc_o = self.theo_wc_o = self.mean_o = 0
        self.theo_bc_i = self.theo_wc_i =  self.mean_i = 0


@dataclass()
class ExperimentResult:
    page_count: int = 0
    insert: ExperimentOperationResult = field(default_factory=ExperimentOperationResult)
    search: ExperimentOperationResult = field(default_factory=ExperimentOperationResult)
    update: ExperimentOperationResult = field(default_factory=ExperimentOperationResult)
    delete: ExperimentOperationResult = field(default_factory=ExperimentOperationResult)
    def reset(self):
        self.page_count = 0
        self.insert.reset()
        self.search.reset()
        self.update.reset()
        self.delete.reset()




class TreeExperimentRunner:

    _tree: BplusTree
    _tree_config: BplusTreeConfig
    _metrics: Metrics

    #config
    print_info: bool
    use_real_height: bool
    TEMP_PATH_STR: ClassVar[str] = "experiment/table/temp"
    MAIN_PATH_STR: ClassVar[str] = "experiment/table/main"

    _operations_delta: int
    _data: List[
        ExperimentDegrees.DATA_TYPE |
        ExperimentRecords.DATA_TYPE
    ]
    _result: ExperimentResult
    _results: List[ExperimentResult]

    AVAILABLE_KEYS_FACTOR: ClassVar[int] = 10
    _static_keys: List[int]
    _operation_keys: List[int]


    def __init__(self):
        self._metrics = Metrics()
        conf = BplusTreeConfig(filepath=self.MAIN_PATH_STR, override_file=True)
        self._tree = BplusTree(conf)
        self._tree.set_metrics(self._metrics)

        self._results = []
        self._data = []
        self._result = ExperimentResult()
        self._operations_delta = 0
        self._static_keys = []
        self._operation_keys = []

        self.print_info = True
        self.use_real_height = True
        self.type = "None"

    def run_experiment_degrees(self, exp: ExperimentDegrees):
        self._data = exp.data
        self._operations_delta = exp.operation_amount
        self._results = []
        N = exp.rec_amount

        if self.print_info: print(f"Experiment Started, Operations amount: {self._operations_delta}")
        i: int = 1
        for d, r in self._data:
            if self.print_info: print(f"Iteration {i}, Records: {N}, d: {d}, r: {r}")
            conf = BplusTreeConfig(d=d, r=r, auto_page_size=True, auto_degrees=False
                                   ,filepath=self.MAIN_PATH_STR)
            self._tree.set_conf_by_instance(conf)

            self.run_iteration(N)
            self._results.append(copy.deepcopy(self._result))
            i += 1


    def run_experiment_records(self, exp: ExperimentRecords):

        self._data = exp.data
        self._operations_delta = exp.operation_amount
        self._results = []
        d, r = exp.node_degree, exp.leaf_degree

        conf = BplusTreeConfig(d=d, r=r, auto_page_size=True,
                               auto_degrees=False, filepath=self.MAIN_PATH_STR)
        self._tree.set_conf_by_instance(conf)

        if self.print_info: print(f"Experiment Started, Operations amount: {self._operations_delta}")
        i: int = 1
        for N in self._data:
            if self.print_info: print(f"Iteration {i}, Records: {N}, d: {d}, r: {r}")
            self.run_iteration(N)
            self._results.append(copy.deepcopy(self._result))
            i += 1
        return None


    def _generate_keys_from_scope(self, static_keys_amount: int):
        keys_amount = static_keys_amount + self._operations_delta
        keys_space = keys_amount * self.AVAILABLE_KEYS_FACTOR

        keys = random.sample(range(keys_space), k=keys_amount)

        self._static_keys = keys[:static_keys_amount]
        self._operation_keys = keys[static_keys_amount:]


    def run_iteration(self, records_amount: int):
        self._tree.reload_file(override=True)
        self._generate_keys_from_scope(records_amount)

        for key in self._static_keys:
            self._tree.insert(key, Record.random())

        self._metrics.reset()
        self._result.reset()

        if self.use_real_height: self._calculate_theo_result(self._tree.height, self._tree.height)
        else:
            d = self._tree.get_conf_attribute("d")
            r = self._tree.get_conf_attribute("r")
            self._calculate_theo_result(*self._calculate_theo_heights(records_amount, d,r))


        self._result.page_count = self._metrics.page_count
        self._calculate_mean_insert_result()
        self._calculate_mean_delete_result()
        self._calculate_mean_search_result()
        self._calculate_mean_update_result()

    def _copy_tree_file_to_temp(self):
        src = Path(self._tree.get_conf_attribute("filepath"))
        dst = Path(self.TEMP_PATH_STR)
        src.copy(dst)

    def _get_temp_tree(self) -> Tuple[BplusTree, Metrics]:
        self._copy_tree_file_to_temp()
        conf = self._tree.get_conf_copy()
        temp_tree = BplusTree(conf)

        metrics = Metrics()
        temp_tree.set_conf_attribute(filepath=self.TEMP_PATH_STR)
        temp_tree.set_metrics(metrics)
        temp_tree.reload_file(override=False)
        return temp_tree, metrics

    def _calculate_mean_insert_result(self):
        temp_tree, metrics = self._get_temp_tree()

        for key in self._operation_keys:
            temp_tree.insert(key, Record.random())
        self._result.insert.mean_i = metrics.i / self._operations_delta
        self._result.insert.mean_o = metrics.o / self._operations_delta

    def _calculate_mean_delete_result(self):
        temp_tree, metrics = self._get_temp_tree()

        keys = random.sample(self._static_keys, k=self._operations_delta)
        for key in keys:
            temp_tree.delete(key)

        self._result.delete.mean_i = metrics.i / self._operations_delta
        self._result.delete.mean_o = metrics.o / self._operations_delta

    def _calculate_mean_update_result(self):
        temp_tree, metrics = self._get_temp_tree()
        new_keys_update_amount = int(self._operations_delta * 0.5)

        keys = random.sample(self._static_keys, k=self._operations_delta)
        new_keys = random.sample(self._operation_keys, k=new_keys_update_amount)

        for key, new_key in zip(keys, new_keys):
            temp_tree.search(key)
            temp_tree.update(key, new_key, Record.random())

        remaining_keys = keys[len(new_keys):]

        for key in remaining_keys:
            temp_tree.search(key)
            temp_tree.update(key,key, Record.random())


        self._result.update.mean_i = metrics.i / self._operations_delta
        self._result.update.mean_o = metrics.o / self._operations_delta

    def _calculate_mean_search_result(self):
        temp_tree, metrics = self._get_temp_tree()

        keys = random.sample(self._static_keys, k=self._operations_delta)
        for key in keys:
            temp_tree.search(key)

        self._result.search.mean_i = metrics.i / self._operations_delta
        self._result.search.mean_o = metrics.o / self._operations_delta

    def _calculate_theo_heights(self, records_amount: int, d: int, r: int) -> Tuple[int, int]:
        N = records_amount
        min_height = int(math.log(N/(2*r),(2*d+1)))
        max_height = int(math.log(N/(2*r), (d+1)))
        return min_height, max_height

    def _calculate_theo_result(self, min_height: int = 0, max_height: int = 0):
        # INSERT
        # from leafs, if always split we read page, left, right up to root
        self._result.insert.theo_wc_i = 3 * (max_height - 1) + 1
        #from leafs, we write either (page,left), (page,right) or (page,new) = 2, then split root = 3 writes
        self._result.insert.theo_wc_o = 2 * (max_height-1) + 3
        #we read until reach leaf
        self._result.insert.theo_bc_i = min_height
        #we read until reach leaf
        self._result.insert.theo_bc_o = 1


        # DELETE
        # from leafs, if always merge we read page, left, right up to root
        self._result.delete.theo_wc_i = 3 * (max_height - 1) + 1
        # from leafs, we write either (page,left), (page,right) = 2, then merge root
        self._result.delete.theo_wc_o =  2*(max_height-1) + 1
        # we read until reach leaf
        self._result.delete.theo_bc_i = min_height
        # we read until reach leaf
        self._result.delete.theo_bc_o = 1


        # SEARCH no Writes
        self._result.search.theo_wc_i = max_height
        self._result.search.theo_wc_o = 0
        self._result.search.theo_bc_i = min_height
        self._result.search.theo_bc_o = 0


        # UPDATE worst case new_key (delete plus update) // 2 because buffer flushed after 2 operations, best case change record
        self._result.update.theo_wc_i = (self._result.insert.theo_wc_i + self._result.delete.theo_wc_i)
        self._result.update.theo_wc_o = (self._result.insert.theo_wc_o + self._result.delete.theo_wc_o)
        self._result.update.theo_bc_o = 1
        self._result.update.theo_bc_i = min_height

    def print_chart(self):
        if not self._data or not self._results:
            raise RuntimeError("No experiment data to display")

        if len(self._data) != len(self._results):
            raise RuntimeError("Data and results length mismatch")

        # X-axis labels
        if isinstance(self._data[0], tuple):
            x_labels = [f"({d},{r})" for d, r in self._data]
        else:
            x_labels = list(map(str, self._data))

        x = range(len(x_labels))

        ops = [
            ("Insert", "insert"),
            ("Delete", "delete"),
            ("Search", "search"),
            ("Update", "update"),
        ]

        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        axes = axes.flatten()

        line_cfg = [
            ("theo_wc_i", "WC read", "--", "o"),
            ("theo_wc_o", "WC write", "--", "s"),
            ("theo_bc_i", "BC read", "-.", "^"),
            ("theo_bc_o", "BC write", "-.", "v"),
            ("mean_i", "Mean read", "-", "x"),
            ("mean_o", "Mean write", "-", "+"),
        ]

        x_label_str = "Records" if self.type == "records" else "Degrees (d, r)"

        # ---- CRUD charts ----
        for idx, (title, attr) in enumerate(ops):
            ax = axes[idx]

            for field, label, style, marker in line_cfg:
                y = [getattr(getattr(r, attr), field) for r in self._results]
                ax.plot(x, y, linestyle=style, marker=marker, label=label)

            ax.set_title(title)
            ax.set_xlabel(x_label_str)
            ax.set_ylabel("Page operations")
            ax.set_xticks(x)
            ax.set_xticklabels(x_labels, rotation=45)
            ax.grid(True)
            ax.legend(fontsize=8)

        # ---- Page count chart ----
        ax = axes[4]
        y_pages = [r.page_count for r in self._results]
        ax.plot(x, y_pages, marker="o")
        ax.set_title("Page count")
        ax.set_xlabel(x_label_str)
        ax.set_ylabel("Pages")
        ax.set_xticks(x)
        ax.set_xticklabels(x_labels, rotation=45)
        ax.grid(True)

        # ---- Hide unused subplot (index 5) ----
        axes[5].axis("off")

        plt.tight_layout()
        plt.show()

    def print_table(self):
        if not self._data or not self._results:
            raise RuntimeError("No experiment data to display")

        if len(self._data) != len(self._results):
            raise RuntimeError("Data and results length mismatch")

        # ---- Row labels ----
        if isinstance(self._data[0], tuple):
            row_labels = [f"({d},{r})" for d, r in self._data]
        else:
            row_labels = list(map(str, self._data))

        # ---- Short labels ----
        ops = {
            "insert": "I",
            "delete": "D",
            "search": "S",
            "update": "U",
        }

        metrics = [
            ("WC-R", "theo_wc_i"),
            ("WC-W", "theo_wc_o"),
            ("BC-R", "theo_bc_i"),
            ("BC-W", "theo_bc_o"),
            ("μ-R", "mean_i"),
            ("μ-W", "mean_o"),
        ]

        # ---- Column labels ----
        col_labels = [
            f"{op_label} {metric_label}"
            for op_label in ops.values()
            for metric_label, _ in metrics
        ]

        # ---- Table values ----
        table_data = []

        for r in self._results:
            row = []
            for op in ops.keys():
                obj = getattr(r, op)
                for _, field in metrics:
                    val = getattr(obj, field)
                    row.append(f"{val:.2f}")
            table_data.append(row)

        # ---- Plot ----
        fig, ax = plt.subplots(
            figsize=(len(col_labels) * 0.55, len(row_labels) * 0.6)
        )
        ax.axis("off")

        table = ax.table(
            cellText=table_data,
            colLabels=col_labels,
            rowLabels=row_labels,
            loc="center",
            cellLoc="center",
        )

        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.6)

        ax.set_title("B+Tree Experiment Results", fontsize=14, pad=20)

        plt.tight_layout()
        plt.show()
