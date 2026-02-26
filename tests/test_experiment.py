from experiment.experiment_data import ExperimentDegrees,ExperimentRecords
from experiment.tree_experiment_runner import TreeExperimentRunner

def test_experiment_records():
    experiment = TreeExperimentRunner()
    experiment.run_experiment_records(ExperimentRecords.DEFAULT)
    experiment.print_chart()

def test_experiment_degrees():
    experiment = TreeExperimentRunner()
    experiment.run_experiment_degrees(ExperimentDegrees.DEFAULT)
    experiment.print_chart()

def test_experiment_degrees_reverse():
    experiment = TreeExperimentRunner()
    experiment.run_experiment_degrees(ExperimentDegrees.REVERSE_DEFAULT)
    experiment.print_chart()