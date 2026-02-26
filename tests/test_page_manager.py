from core.config import BplusTreeConfig
from core.page_manager import PageManager
from core.structures.page import PageType
from core.structures.file_header import FileHeader
from core.structures.record import Record
from experiment.metrics import Metrics


def test_alloc_node():
    conf = BplusTreeConfig(
        r=2, d=2,
        auto_page_size=True, auto_degrees=False, override_file=True)
    loader = PageManager(conf)
    conf.override_file = False

    # new Page
    page = loader.page_alloc(is_leaf=False)

    keys = [1, 2, 3]
    pointers = [0,1,2,3]
    page.keys = keys
    page.pointers = pointers
    page.header.key_count = len(keys)

    loader.buff_flush()
    loader.buff_clear()

    page_test = loader.page_read(page.header.id)
    assert (page == page_test)

    # page from free
    loader.page_dealloc(page)

    loader.buff_flush()
    loader.buff_clear()

    page = loader.page_alloc(is_leaf=False)
    keys = [1, 2, 3]
    pointers = [0,1,2,3]
    page.keys = keys
    page.pointers = pointers
    page.header.key_count = len(keys)

    loader.buff_flush()
    loader.buff_clear()

    page_test = loader.page_read(page.header.id)
    assert (page == page_test)

    root = loader.get_root()
    root.header.type = PageType.INTERNAL
    root.keys = keys
    root.pointers = pointers
    root.header.key_count = len(keys)
    root.dirty = True

    loader.buff_flush()
    loader.buff_clear()

    root_test = loader.page_read(root.header.id)
    assert (root == root_test)

    loader.file_load()

    root_test = loader.page_read(root.header.id)
    assert (root == root_test)

def test_alloc_Leaf():
    conf = BplusTreeConfig(
        r=2, d=2,
        auto_page_size=True, auto_degrees=False, override_file=True)
    loader = PageManager(conf)
    conf.override_file = False


    #new Page
    page = loader.page_alloc(True)

    keys = [1,2,3]
    records = [Record(1.0,1.0), Record(1.0, 2.0), Record(3.0, 2.4)]
    page.keys = keys
    page.records = records
    page.header.key_count = len(keys)

    loader.buff_flush()
    loader.buff_clear()

    page_test = loader.page_read(page.header.id)
    assert(page == page_test)

    #page from free
    loader.page_dealloc(page)

    loader.buff_flush()
    loader.buff_clear()

    page = loader.page_alloc(is_leaf=True)
    keys = [1, 2, 3]
    records = [Record(1.0, 1.0), Record(1.0, 2.0), Record(3.0, 2.4)]
    page.keys = keys
    page.records = records
    page.header.key_count = len(keys)

    loader.buff_flush()
    loader.buff_clear()

    page_test = loader.page_read(page.header.id)
    assert (page == page_test)

    root = loader.get_root()
    root.keys = keys
    root.records = records
    root.header.key_count = len(keys)
    root.dirty = True

    loader.buff_flush()
    loader.buff_clear()

    root_test = loader.page_read(root.header.id)
    assert (root == root_test)

    loader.file_load()

    root_test = loader.page_read(root.header.id)
    assert (root == root_test)

def test_metrics_compatibility():
    conf = BplusTreeConfig(
        r=2, d=2,
        auto_page_size=True, auto_degrees=False, override_file=True)
    metrics = Metrics()
    loader = PageManager(conf)
    loader.set_metrics(metrics)

    conf.override_file = False
    assert metrics.page_count == loader._page_count

    page = loader.page_alloc(True)
    assert metrics.page_count == loader._page_count == 3

    loader.page_dealloc(page)
    assert metrics.page_count == loader._page_count == 3

    loader.file_load()
    assert metrics.page_count == loader._page_count == 3

def test_file():
    conf = BplusTreeConfig(
        r=2, d=2,
        auto_page_size=True, auto_degrees=False, override_file=True)
    loader = PageManager(conf)

    loader.buff_flush()
    loader.buff_clear()

    conf.override_file = False
    loader.file_load()
    assert loader._file_header == FileHeader(conf.page_size, magic=conf.magic)

def test_page_allocation():
    conf = BplusTreeConfig(
        r=2, d=2,
        auto_page_size=True, auto_degrees=False, override_file=True)
    loader = PageManager(conf)

    conf.override_file = False
    assert loader._page_count == 2

    page = loader.page_alloc(True)
    assert loader._page_count == 3

    loader.page_dealloc(page)
    assert loader._page_count == 3
    assert loader._file_header.free_pages_head == 2

    page1 = loader.page_alloc(True)
    assert loader._page_count == 3
    assert loader._file_header.free_pages_head == 0

    page2 = loader.page_alloc(True)
    assert loader._page_count == 4
    assert loader._file_header.free_pages_head == 0

    loader.page_dealloc(page1)
    assert loader._page_count == 4
    assert loader._file_header.free_pages_head == 2

    loader.page_dealloc(page2)
    assert loader._page_count == 4
    assert loader._file_header.free_pages_head == 3

    loader.file_load()

    assert loader._file_header.free_pages_head == 3
    assert loader._file_header.root_page_id == 1

    page1 = loader.page_alloc(True)
    assert loader._page_count == 4
    assert loader._file_header.free_pages_head == 2

    page2 = loader.page_alloc(True)
    assert loader._page_count == 4
    assert loader._file_header.free_pages_head == 0

    page3 = loader.page_alloc(True)
    assert loader._page_count == 5
    assert loader._file_header.free_pages_head == 0
    assert loader._file_header.root_page_id == 1
    assert loader._file_header.magic == conf.magic

    loader.buff_flush()
    loader.buff_clear()

    page2_copy = loader.page_read(page2.header.id)
    assert page2 == page2_copy

    loader.file_load()

    page2_copy = loader.page_read(page2.header.id)
    assert page2 == page2_copy



