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
        auto_page_size=True,auto_degrees=False,override_file=True,  filepath="./tests/table/main_file")

def test_update_same_key():
    t = BplusTree(conf=conf)
    t.set_conf_by_template("presentation")

    t.insert(10, Record(1.0, 1.0))
    t.update(10, 10, Record(2.0, 3.0))

    rec = t.search(10)
    assert rec.mass == 2.0
    assert rec.velocity == 3.0

    t.display("structure_collapse_rec")

def test_non_equal_r_d_root_capacity_change():
    new_conf = copy.deepcopy(conf)
    new_conf.d = 2
    new_conf.r = 4
    t = BplusTree(conf=new_conf)
    for i in range(1,60):
        t.insert(i, Record.random())
        t.display("structure_collapse_rec", f"{i}")
        r = t._loader.get_root()
        if r.is_leaf:
            assert r.header.key_count <= new_conf.max_keys_leaf
        else:
            assert r.header.key_count <= new_conf.max_keys_node

def test_update_merge_then_split():
    t = BplusTree(conf=conf)

    i: int = 0
    for i in range(16):
        t.insert(i, Record(1.0, 1.0))
        t.display("structure_collapse_rec", f"{i}")
    t.insert(i+1, Record(1.0, 1.0))
    t.display("structure_collapse_rec", f"{i}")

    # forces delete merge
    t.update(15, 100, Record(5.0, 5.0))

    with pytest.raises(ValueError):
        assert t.search(15) is None
    assert t.search(100) is not None

    t.display("structure_collapse_rec")

def test_search_after_rebalance():
    t = BplusTree(conf=conf)

    keys = [5, 10, 15, 20, 25, 30]
    for k in keys:
        t.insert(k, Record(k, k))

    t.delete(15)

    for k in keys:
        if k != 15:
            assert t.search(k) is not None

def test_random_insert_delete():
    conf.duplicates_keys_in_nodes_allowed = True
    t = BplusTree(conf)
    i: int = 100
    iterations: int = 2
    try:
        for it in range(iterations):
            print(f"Iteration: {it}")
            keys = random.sample(range(i), k=i)
            for key in keys:
                t.insert(key, Record.random())

            delete_keys: List = random.sample(range(i), k=i)
            key: int = 0
            z = i
            divisor = z // 2

            for key in delete_keys[:]:
                t.delete(key)
                delete_keys.remove(key)
                if z % divisor == 0:
                    t.display("structure_collapse_rec", f"d:{key}")
                assert_existing_keys_can_be_found(t, delete_keys)
                z -= 1
            t.display("structure_collapse_rec", f"d:{key}")
    except Exception:
        raise

def assert_existing_keys_can_be_found(t: BplusTree, keys: List[int]):
    for key in keys:
       t.search(key)
    assert True
