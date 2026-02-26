import copy
import random
from random import Random
from typing import List

import pytest

from core.bplus_tree import BplusTree, BplusTreeConfig
from core.structures.page import Page
from core.structures.record import Record

conf = BplusTreeConfig(
        d=2,r=2,page_size=128,debug=True,
        auto_page_size=True,auto_degrees=False,override_file=True)

def test_update_bigger_tree():
    t = BplusTree(conf=conf)
    for i in range(1,300):
        t.insert(i, Record.random())
    t.display(mode="structure_collapse_rec", tittle="Before Update")
    t.update(299, 0, Record.random())
    t.display(mode="structure_collapse_rec", tittle="After Update")

def test_borrow_only_no_merge():
    t = BplusTree(conf=conf)

    for i in range(1, 10):
        t.insert(i, Record(1.0, 1.0))

    t.display("structure_collapse_rec")
    # delete one key to trigger underflow
    t.delete(8)

    # assert height unchanged
    t.display("structure_collapse_rec")

    t.delete(5)
    t.display("structure_collapse_rec")

def test_printing():
    t = BplusTree(conf=conf)
    i: int = 0
    for i in range(32):
        t.insert(i, Record(1.0, 1.0))
        print(i)
        t.display("structure_collapse_rec")
    t.insert(i+1, Record(1.0, 1.0))
    t.display("structure_collapse_rec")

def test_right_to_right_ops():
    t = BplusTree(conf=conf)

    for i in range(100):
        t.insert(i, Record(1.0, 1.0))
        t.display("structure_collapse_rec")

    for i in range(100):
        t.delete(i)
        t.display("structure_collapse_rec")

def test_left_to_left_ops():
    t = BplusTree(conf=conf)

    for i in range(100, 0, -1):
        t.insert(i, Record(1.0, 1.0))
        t.display("structure_collapse_rec")

    for i in range(100, 0, -1):
        t.delete(i)
        t.display("structure_collapse_rec")

def test_right_to_left_ops():
    t = BplusTree(conf=conf)
    i: int = 0
    for i in range(70, 0, -1):
        t.insert(i, Record(2.0, 2.0))
        t.display("structure_collapse_rec")
    t.display("structure_collapse_rec")
    for i in  range(1, 71, 1):
        t.delete(i)
        t.display("structure_collapse_rec")

def test_left_to_right_ops():
    t = BplusTree(conf=conf)
    i: int = 0
    for i in range(1, 71, 1):
        t.insert(i, Record(2.0, 2.0))
        t.display("structure_collapse_rec")
    t.display("structure_collapse_rec")
    for i in range(70, 0, -1):
        t.delete(i)
        t.display("structure_collapse_rec")

def test_split_merge_root_leaf():
    t = BplusTree(conf=conf)

    t.insert(0, Record(2.0, 2.0))
    t.insert(2, Record(2.0, 2.0))
    t.insert(1, Record(2.0, 2.0))
    t.insert(4, Record(2.0, 2.0))
    t.display("structure_collapse_rec")

    t.insert(3, Record(2.0, 2.0))

    t.delete(4)
    t.display("structure_collapse_rec")
    t.delete(0)
    t.display("structure_collapse_rec")

def test_split_merge_root_node():
    t = BplusTree(conf=conf)

    i: int = 0
    for i in range(20):
        t.insert(i, Record(2.0, 2.0))
    print("root before split")
    t.display("structure_collapse_rec")

    #split root as node
    i += 1
    t.insert(i, Record(2.0, 2.0))
    print("root after split, i:20")
    t.display("structure_collapse_rec")

    t.delete(20)
    print("root before merge")
    t.display("structure_collapse_rec")

    t.delete(19)
    print("root after merge, d: 19")
    t.display("structure_collapse_rec")



