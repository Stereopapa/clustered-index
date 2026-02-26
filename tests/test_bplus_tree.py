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
    i: int = 3000
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

# """
# def test_leafs_max_equal_parent_key():
#     conf.duplicates_keys_in_nodes_allowed = True
#     t = BplusTree(conf)
#     i: int = 100
#     try:
#         keys = random.sample(range(i), k=i)
#         for key in keys:
#             t.insert(key, Record.random())
#
#         delete_keys = random.sample(range(i), k=i)
#         key: int = 0
#         divisor = i//10
#         for key in delete_keys:
#             t.delete(key)
#             if i % divisor == 0:
#                 t.display("structure_collapse_rec", f"d:{key}")
#             assert_leafs_max_equals_parent_keys(t)
#             i -= 1
#         t.display("structure_collapse_rec", f"d:{key}")
#     except Exception:
#         raise
#
# def test_find_error_merging_():
#     t = BplusTree(conf)
#     keys = [2, 27, 30, 9, 13, 22, 19, 42, 25, 17, 43, 18, 36, 14, 23, 31, 15, 10, 48, 34, 8, 45, 44, 26, 47, 11, 41, 28, 20, 6, 12, 0, 7, 16, 40, 21, 37, 24, 39, 38, 32, 29, 3, 1, 46, 4, 35, 5, 49, 33]
#     del_keys = [2, 35, 28, 27, 9, 17, 22, 29, 30, 25, 23, 24, 11, 12, 42, 14, 1, 41, 44, 38, 7, 46, 26, 34, 6, 39, 45, 15, 20, 13, 48, 16, 0, 47, 4, 32, 19, 33, 40, 37, 43, 18, 5, 8, 21, 10, 3, 36, 49, 31]
#     try:
#         for key in keys:
#             t.insert(key, Record.random())
#         t.display("structure_collapse_rec", f"d:{-1}")
#         for key in del_keys:
#             t.delete(key)
#             t.display("structure_collapse_rec", f"d:{key}")
#             assert_leafs_max_equals_parent_keys(t)
#     except Exception:
#         raise
#
# def assert_leafs_max_equals_parent_keys(t: BplusTree):
#     page, _ = t._descent_tree(0)
#     if not page.is_root:
#         parent =  t._loader.page_read(page.header.parent)
#     idx: int = -1
#     while not page.is_root:
#         if parent.header.id != page.header.parent:
#             idx = 0
#             parent = t._loader.page_read(page.header.parent)
#         else: idx += 1
#         if idx < len(parent.keys):
#             assert parent.keys[idx] == max(page.keys) == page.keys[-1]
#         page = t._loader.page_read(page.header.next)
#         if page.header.next == 0:
#             break
# def test_rightmost_record_delete():
#     t = BplusTree(conf=conf)
#     for i in range(100):
#         t.insert(i, Record.random())
#     t.display(mode="structure_collapse_rec")
#
#     key = 95
#
#     page, ch_pos = t._descent_tree(key)
#     parent = t._loader.page_read(page.header.parent)
#     t.delete(key)
#     assert parent.keys[-1] == page.keys[-1]
#     t.delete(99)
#     assert parent.keys[-1] == page.keys[-1]
#
#     t.display(mode="structure_collapse_rec")
