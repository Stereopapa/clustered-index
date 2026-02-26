import pytest

from core.config import BplusTreeConfig

def test_auto_page_size():
    conf = BplusTreeConfig(
        r = 2, d = 2,
        auto_page_size=True, auto_degrees=False)
    #head size = 21, leaf_size = 12, node_size = 8, max(size_d, size_r), 48+21=69 round to 2^x = 128
    assert conf.page_size == 128

    conf = BplusTreeConfig(
        d=10,r=2,
        auto_page_size=True, auto_degrees=False)
    # head size = 21, leaf_size = 12, node_size = 8, 160 + 21 = 181 round to 2^x = 256
    assert conf.page_size == 256

    conf = BplusTreeConfig(
        r=4,d=2,
        auto_page_size=True, auto_degrees=False)
    # head size = 21, leaf_size = 12, node_size = 8, 96+21=117 round to 2^x = 128
    assert conf.page_size == 128
    with pytest.raises(ValueError):
        conf.page_size = 256

def test_auto_degrees():
    conf = BplusTreeConfig(
        d=2, r=2, page_size=128,
        auto_page_size=False, auto_degrees=True)
    conf.auto_degrees = True
    # head size = 21, leaf_size = 12, node_size = 8, 128-21=43, r=107//12)//2=4, d=107//8)//2=6
    assert conf.r == 4 and conf.d == 6
    with pytest.raises(ValueError):
        conf.d = 32
    with pytest.raises(ValueError):
        conf.r = 32

def test_page_size_validation():
    conf = BplusTreeConfig(
        d=2, r=2, page_size=128,
        auto_page_size=False, auto_degrees=False)

    with pytest.raises(ValueError):
        conf.page_size = 132
    with pytest.raises(ValueError):
        conf.page_size = 64
    with pytest.raises(ValueError):
        conf.page_size = 128 * 2^10


def test_degree_validation():
    conf = BplusTreeConfig(
            d=2, r=2, page_size=128,
            auto_page_size=False, auto_degrees=False)
    with pytest.raises(ValueError):
        conf.d = 100