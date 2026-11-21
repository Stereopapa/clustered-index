from core.bplus_tree import BplusTree
from core.config import BplusTreeConfig
from experiment.experiment_data import ExperimentDegrees,ExperimentRecords
from experiment.metrics import Metrics
from experiment.tree_experiment_runner import TreeExperimentRunner
from unittest.mock import patch

def new_runner() -> TreeExperimentRunner:
    conf = BplusTreeConfig(filepath=TreeExperimentRunner.MAIN_PATH_STR, override_file=True)
    return TreeExperimentRunner(BplusTree(conf), Metrics())

@patch("experiment.tree_experiment_runner.TreeExperimentRunner.RESULT_CHART_PATH_STR", "./tests/docs/charts")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.RESULT_TABLE_PATH_STR", "./tests/docs/tables")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.TEMP_PATH_STR", "./tests/experiment/table/temp")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.MAIN_PATH_STR", "./tests/experiment/table/main")
def test_experiment_records():
    experiment = new_runner()
    experiment.save_chart_and_table = True
    experiment.run_experiment(ExperimentRecords.DEFAULT)

@patch("experiment.tree_experiment_runner.TreeExperimentRunner.RESULT_CHART_PATH_STR", "./tests/docs/charts")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.RESULT_TABLE_PATH_STR", "./tests/docs/tables")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.TEMP_PATH_STR", "./tests/experiment/table/temp")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.MAIN_PATH_STR", "./tests/experiment/table/main")
def test_experiment_degrees():
    experiment = new_runner()
    experiment.save_chart_and_table = True
    experiment.run_experiment(ExperimentDegrees.DEFAULT)

@patch("experiment.tree_experiment_runner.TreeExperimentRunner.RESULT_CHART_PATH_STR", "./tests/docs/charts")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.RESULT_TABLE_PATH_STR", "./tests/docs/tables")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.TEMP_PATH_STR", "./tests/experiment/table/temp")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.MAIN_PATH_STR", "./tests/experiment/table/main")
def test_experiment_degrees_reverse():
    experiment = new_runner()
    experiment.save_chart_and_table = True
    experiment.run_experiment(ExperimentDegrees.REVERSE_DEFAULT)