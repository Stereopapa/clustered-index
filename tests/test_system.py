def test_system():
    from core.bplus_tree import BplusTree
    from experiment.metrics import Metrics
    from experiment.tree_experiment_runner import TreeExperimentRunner
    from tui import Tui



    tree_experiment_runner = TreeExperimentRunner()
    tree = BplusTree()
    interface = Tui(tree, tree_experiment_runner)
    interface.run()