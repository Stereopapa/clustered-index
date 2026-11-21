from core.bplus_tree import BplusTree, BplusTreeConfig
from experiment.metrics import Metrics
from experiment.tree_experiment_runner import TreeExperimentRunner
from tui import Tui

conf = BplusTreeConfig.PRESENTATION
experiment_conf = BplusTreeConfig(filepath=TreeExperimentRunner.MAIN_PATH_STR, override_file=True)
t_experiment_runner = TreeExperimentRunner(BplusTree(experiment_conf), Metrics())
tree = BplusTree(conf)

interface = Tui(tree, t_experiment_runner)

if __name__ == "__main__":
    interface.run()