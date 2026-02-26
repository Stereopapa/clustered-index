import math
import struct
from dataclasses import dataclass
from typing import TypedDict, ClassVar, Literal

from core.structures.page import PageHeader, Page
from core.structures.record import Record
from utils import pow_range



@dataclass
class BplusTreeConfig:

    class SeterDict(TypedDict, total=False):
        debug: bool
        filepath: str
        override_file: bool
        auto_degrees: bool
        auto_page_size: bool
        page_size: int
        d: int
        r: int

    GetterLiteral = Literal[
    "debug", "filepath", "override_file", "auto_degrees",
    "auto_page_size", "page_size", "d", "r"
    ]


    _MAGIC: ClassVar[bytes] = b"B+Tr"
    @property
    def magic(self): return self._MAGIC
    d: int = 2
    @property
    def max_keys_node(self): return 2 * self.d
    r: int = 2
    @property
    def max_keys_leaf(self): return 2 * self.r

    page_size: int = 4096
    debug: bool = False
    filepath: str = "data/main_file"
    override_file: bool = False

    auto_degrees: bool = True
    auto_page_size: bool = False

    _initialized: bool = False


    MAX_PAGE_SIZE: ClassVar[int] = 64 * 2 ** 10
    MIN_PAGE_SIZE: ClassVar[int] = 128
    PRESENTATION: ClassVar['BplusTreeConfig']
    DEFAULT: ClassVar['BplusTreeConfig']



    def __post_init__(self):
        self._initialized = True

    def __setattr__(self, key, value):

        if getattr(self, '_initialized') is True:
            self._pre_set_check(key, value)
        object.__setattr__(self, key, value)
        self._post_set_check(key, value)

    def _pre_set_check(self, key, value):
        match key:
            case "r":  self.validate_r(value)
            case "d": self.validate_d(value)
            case "page_size": self.validate_page_size(value)

    def _post_set_check(self, key, value):
        match key:
            case "page_size":
                if self.auto_degrees and self._initialized :
                    self.set_auto_degrees()
            case "r" | "d" :
                if self.auto_page_size and self._initialized :
                    self.set_auto_page_size()
            case "auto_page_size":
                if value: self.set_auto_page_size()
            case "auto_degrees":
                if value: self.set_auto_degrees()


    def validate_page_size(self, page_size: int):
        if self.auto_page_size:
            raise ValueError("Cannot set page_size in auto page size mode")
        if page_size < self.MIN_PAGE_SIZE:
            raise ValueError(f"page size {page_size}B fell short to Min page size {self.MIN_PAGE_SIZE}")
        if page_size > self.MAX_PAGE_SIZE:
            raise ValueError(f"page size {page_size // (2 ** 10)}KB exceeded Max page size {self.MAX_PAGE_SIZE}")
        if not any(page_size == size for size in pow_range(self.MIN_PAGE_SIZE,self.MAX_PAGE_SIZE*2)):
            raise ValueError(f"page size {page_size // (2 ** 10)}B need to be a power of 2")

    def validate_r(self, r: int):
        if self.auto_degrees:
            raise ValueError("Cannot set leaf degree in auto degree mode")
        if r < 0:
            raise ValueError(f"leaf degree {r} is wrong, must be positive value")
        size = PageHeader.BYTES_SIZE + struct.calcsize((Page.LEAF_FMT * r))
        if size > self.page_size:
            raise ValueError(f"Leaf degree: {r} is to big: {size} to fit into page: {self.page_size}")

    def validate_d(self, d: int):
        if self.auto_degrees:
            raise ValueError("Cannot set Node degree in auto degree mode")
        if d < 0:
            raise ValueError(F"Node degree {d} is wrong, must be positive value")
        size = PageHeader.BYTES_SIZE + struct.calcsize((Page.LEAF_FMT * d))
        if size > self.page_size:
            raise ValueError(f"Node degree: {d} is to big: {size} to fit into page: {self.page_size}")

    def set_auto_degrees(self):
        if self.auto_page_size:
            raise ValueError(f"Auto degree mode cannot be set with auto page size mode")
        object.__setattr__(self,'auto_degrees', True)

        h_size = PageHeader.BYTES_SIZE
        available = self.page_size - h_size

        tup_size_r = struct.calcsize(Page.LEAF_FMT) + Record.BYTES_SIZE
        tup_size_d = struct.calcsize(Page.NODE_FMT)

        max_keys_r = available // tup_size_r
        max_keys_d = (available - struct.calcsize(Page.PTR_FMT)) // tup_size_d

        object.__setattr__(self, "r", (max_keys_r // 2))
        object.__setattr__(self, "d", (max_keys_d // 2))

    def set_auto_page_size(self):
        if self.auto_degrees:
            raise ValueError(f"Auto page size mode cannot be set with auto degree mode")
        object.__setattr__(self,'auto_page_size', True)

        h_size = PageHeader.BYTES_SIZE
        tup_size_r = struct.calcsize(Page.LEAF_FMT)
        tup_size_d = struct.calcsize(Page.NODE_FMT)

        r_size = tup_size_r * self.max_keys_leaf
        d_size = tup_size_d * self.max_keys_node + struct.calcsize(Page.PTR_FMT)
        size = max(r_size, d_size) + h_size

        base = 2

        while base < size:
            base *= 2
            if base >= self.MAX_PAGE_SIZE:
                raise ValueError(f"page size {(size // 2**10)}KB exceeded Max page size {self.MAX_PAGE_SIZE}")
        object.__setattr__(self, "page_size", base)


BplusTreeConfig.PRESENTATION = BplusTreeConfig(
        d=2,r=2,page_size=128,debug=False,
        auto_page_size=True,auto_degrees=False,override_file=False)

BplusTreeConfig.DEFAULT = BplusTreeConfig()

