from experiment.experiment_data import ExperimentDegrees,ExperimentRecords
from experiment.tree_experiment_runner import TreeExperimentRunner
from unittest.mock import patch

@patch("experiment.tree_experiment_runner.TreeExperimentRunner.TEMP_PATH_STR", "./tests/experiment/table/temp")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.MAIN_PATH_STR", "./tests/experiment/table/main")
def test_experiment_records():
    experiment = TreeExperimentRunner()
    experiment.run_experiment_records(ExperimentRecords.DEFAULT)
    experiment.print_chart()

@patch("experiment.tree_experiment_runner.TreeExperimentRunner.TEMP_PATH_STR", "./tests/experiment/table/temp")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.MAIN_PATH_STR", "./tests/experiment/table/main")
def test_experiment_degrees():
    experiment = TreeExperimentRunner()
    experiment.run_experiment_degrees(ExperimentDegrees.DEFAULT)
    experiment.print_chart()

@patch("experiment.tree_experiment_runner.TreeExperimentRunner.TEMP_PATH_STR", "./tests/experiment/table/temp")
@patch("experiment.tree_experiment_runner.TreeExperimentRunner.MAIN_PATH_STR", "./tests/experiment/table/main")
def test_experiment_degrees_reverse():
    experiment = TreeExperimentRunner()
    experiment.run_experiment_degrees(ExperimentDegrees.REVERSE_DEFAULT)
    experiment.print_chart()