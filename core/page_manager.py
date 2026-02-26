
from typing import List, BinaryIO
from pathlib import Path

from core.structures.page import Page, PageHeader, PageType
from core.structures.file_header import FileHeader
from core.config import BplusTreeConfig
from experiment.metrics import Metrics



class PageManager:
    MIN_PAGE: int = 1
    _metrics: Metrics
    _pages: List[Page]
    _conf: BplusTreeConfig
    _file_header: FileHeader | None
    _file: BinaryIO | None
    _page_count: int

    def __init__(self, conf: BplusTreeConfig):
        self._conf = conf
        self._pages = []
        self._file = None
        self._file_header = None
        self._page_count = -1
        self.set_metrics()
        self.file_load()

    def __del__(self):
        self._file_close()

    def set_metrics(self, metrics: Metrics = None):
        self._metrics = metrics
        self._update_page_count(self._page_count)


    def _update_page_count(self, val: int):
        if self._metrics: self._metrics.page_count = val
        self._page_count = val

    def _file_header_load(self):
        self._file.seek(0, 0)
        raw = self._file.read(self._conf.page_size)
        self._file_header = FileHeader.from_bytes(raw)

        if self._file_header.page_size != self._conf.page_size:
            raise ValueError("Configuration page size doesn't match file page size")
        if self._file_header.magic != self._conf.magic:
            raise ValueError("Wrong B+ Tree main file format or the file is compromised")

        self._update_page_count(self._file.seek(0,2) // self._file_header.page_size)

    def _file_header_save(self):
        self._file.seek(0, 0)
        self._file.write(bytes(self._file_header))
        self._file_header.dirty = False

    def _init_root(self):
        page = self.page_alloc(True)
        self._file_header.root_page_id = page.header.id
        self._file_header.dirty = True

    def get_root(self) -> Page:
        return self.page_read(self._file_header.root_page_id)


    def _file_init(self):
        self._file_header = FileHeader(
            page_size= self._conf.page_size,
            magic= self._conf.magic,
            root_page_id= 1,
            free_pages_head= 0
        )
        self._file_header.dirty = True

        self._update_page_count(1)
        self._init_root()

        self.buff_flush()
        self.buff_clear()

    def file_load(self):
        self._file_close()

        filepath = Path(self._conf.filepath)
        dictpath = filepath.parent
        dictpath.mkdir(parents=True, exist_ok=True)

        if self._conf.override_file: self._file_delete()

        self._file_create()
        self._file_open()

        #file have data
        if self._file.seek(0, 2) >= self._conf.page_size:
            self._file_header_load()
            self.page_read(self._file_header.root_page_id)

        #empty file
        else:
            self._file_init()


    def _file_create(self):
        filepath = Path(self._conf.filepath)
        filepath.touch(exist_ok=True)

    def _file_delete(self):
        filepath = Path(self._conf.filepath)
        filepath.unlink(missing_ok=True)

    def _file_close(self):
        if self._file:
            self.buff_flush()
            self._pages.clear()
            self._file.flush()
            self._file.close()

    def _file_open(self):
        self._file = Path(self._conf.filepath).open("r+b")
        self._file.flush()

    def _page_save_to_file(self, page: Page):
        out =  bytearray()
        page_bytes =  bytes(page)
        padding = b"\x00" * (self._file_header.page_size - len(page_bytes))

        out += page_bytes
        out += padding

        offset = page.header.id * self._file_header.page_size
        self._file.seek(offset)
        self._file.write(out)

        if self._metrics is not None: self._metrics.o += 1

    def change_page_type(self, page: Page, type: PageType):
        page.header.type = type
        self._page_set_capacity(page)

    def _page_set_capacity(self, page: Page):
        if page.header.type == PageType.LEAF:
            page.header.min_keys = self._conf.r
            page.header.max_keys = self._conf.max_keys_leaf
        elif page.header.type == PageType.INTERNAL:
            page.header.min_keys = self._conf.d
            page.header.max_keys = self._conf.max_keys_node
        else:
            page.header.max_keys = 0
            page.header.max_keys = 0

    def _page_load_from_file(self, page_id: int) -> Page:
        offset = page_id * self._file_header.page_size
        self._file.seek(offset, 0)

        raw = self._file.read(self._file_header.page_size)
        try:
            page = Page.from_bytes(raw)
        except Exception:
            raise

        if self._metrics is not None: self._metrics.i += 1

        self._pages.append(page)
        return page


    def _page_alloc_free(self, is_leaf: bool) -> Page:
        page_id = self._file_header.free_pages_head
        self._file_header.dirty = True

        page = next((p for p in self._pages if p.header.id == page_id), None)
        if not page: page = self._page_load_from_file(page_id)

        self._file_header.free_pages_head = page.header.parent

        if is_leaf: page.header.type = PageType.LEAF
        else: page.header.type = PageType.INTERNAL

        return page

    def _page_alloc_new(self, is_leaf: bool) -> Page:

        page_id = self._page_count
        page_type: PageType
        if is_leaf: page_type = PageType.LEAF
        else: page_type = PageType.INTERNAL

        page = Page(PageHeader(page_type, page_id), [])
        self._pages.append(page)
        self._update_page_count(self._page_count + 1)
        return page

    def page_alloc(self, is_leaf: bool) -> Page:

        page: Page
        page_id: int

        if self._file_header.free_pages_head > 0:
            page = self._page_alloc_free(is_leaf)
        else:
            page = self._page_alloc_new(is_leaf)

        page.dirty = True
        self._page_set_capacity(page)

        return page

    def page_dealloc(self, page: Page):
        if page not in self._pages: self._pages.append(page)

        page.free(self._file_header.free_pages_head)
        self._file_header.free_pages_head = page.header.id
        page.dirty = True


    def buff_flush(self):
        if self._file_header.dirty: self._file_header_save()
        for page in self._pages:
            if page.dirty: self._page_write(page, flush=False)
        self._file.flush()

    def buff_clear(self, force: bool = False):

        if not force and any(page.dirty for page in self._pages):
            raise RuntimeError("Buffer should be flushed before beeing cleaned")

        root_id = self._file_header.root_page_id
        root_page = next((p for p in self._pages if p.header.id == root_id), None)

        self._pages.clear()
        if root_page: self._pages.append(root_page)

    def revert_to_prev_flush(self):
        self._pages.clear()
        self._file_header_load()

    def page_read(self, page_id: int)  -> Page:
        if page_id < 1 or page_id >= self._page_count:
            raise IndexError(f"Page Id {page_id} is out of bounds for reserved 1-{self._page_count - 1} ids")

        page: Page
        for page in self._pages:
            if page.header.id == page_id:
                return page
        page = self._page_load_from_file(page_id)
        self._page_set_capacity(page)
        if page.header.type == PageType.FREE:
            raise RuntimeError("Free Pages are not accessible")

        return page


    def _page_write(self, page: Page, flush: bool = False) -> None:
        if not page.dirty: return
        if page.header.id < 1 or page.header.id >= self._page_count:
            raise IndexError(f"Page Id {page.header.id} is out of bounds for reserved 1-{self._page_count - 1} ids")

        self._page_save_to_file(page)
        page.dirty = False

        if flush: self._file.flush()