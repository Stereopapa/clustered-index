from experiment.experiment_data import ExperimentRecords
from experiment.tree_experiment_runner import TreeExperimentRunner

def tst_experiment():
    experiment = TreeExperimentRunner()
    for _ in range(100):
        experiment.run_experiment_records(ExperimentRecords([1000],1000, 2, 2))
def tst_experiment_2():
    experiment = TreeExperimentRunner()
    experiment.run_experiment_degrees(*TreeExperimentRunner.DEFAULT_DEGREES_EXPERIMENT)
    experiment.print_chart()

tst_experiment()