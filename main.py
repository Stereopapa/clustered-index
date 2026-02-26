from core.bplus_tree import BplusTree, BplusTreeConfig
from experiment.tree_experiment_runner import TreeExperimentRunner
from tui import Tui

conf = BplusTreeConfig.PRESENTATION
t_experiment_runner = TreeExperimentRunner()
tree = BplusTree(conf)

interface = Tui(tree, t_experiment_runner)

if __name__ == "__main__":
    interface.run()