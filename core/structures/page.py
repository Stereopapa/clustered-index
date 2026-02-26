import bisect
import struct
from dataclasses import dataclass, astuple
from turtledemo.penrose import start
from typing import ClassVar
from typing import List, Dict, TypedDict, Tuple
from enum import Enum
from itertools import chain

from pyparsing import identchars

from core.structures.record import Record


class PageType(Enum):
    INTERNAL = 0
    LEAF = 1
    FREE = 2
    def __repr__(self):
        if self.name == "INTERNAL": return "NODE"
        elif self.name == "LEAF": return "LEAF"
        else: return "FREE"

#TODO: slots set to true
@dataclass(slots=False)
class PageHeader:

    type: PageType
    id: int
    parent: int = 0
    key_count: int = 0
    next: int = 0
    prev: int = 0
    max_keys: int = 0
    min_keys: int = 0

    FMT: ClassVar[str] = "<BIIIII"
    BYTES_SIZE: ClassVar[int] = struct.calcsize(FMT)

    def __bytes__(self):
        return struct.pack(
            self.FMT,
            self.type.value, self.id,
            self.parent, self.key_count,
            self.prev, self.next
        )


    @classmethod
    def from_bytes(cls, raw: bytes) -> "PageHeader":
        unpacked = struct.unpack_from(cls.FMT, raw, 0)
        return cls(type=PageType(unpacked[0]), id=unpacked[1],
                   parent=unpacked[2], key_count=unpacked[3],
                   prev=unpacked[4], next=unpacked[5])

    def __repr__(self):
        return (f"id={self.id},type={repr(self.type)},prev={self.prev},next={self.next},parent={self.parent}"
                f",max_k={self.max_keys},min_k={self.min_keys}")


@dataclass(slots=True)
class Page:

    header: PageHeader
    keys: List[int]
    pointers: List[int]
    records: List[Record]

    KEY_FMT: ClassVar[str] = "I"
    PTR_FMT: ClassVar[str] = "I"
    LEAF_FMT: ClassVar[str] = KEY_FMT+Record.FMT
    NODE_FMT: ClassVar[str] = PTR_FMT + KEY_FMT

    #TODO: Move all dirty logic to page

    dirty: bool
    @property
    def is_leaf(self): return self.header.type == PageType.LEAF
    @property
    def is_root(self): return self.header.parent == 0
    @property
    def overflow(self) -> bool:
        if  len(self.keys) > self.header.max_keys:
            return True
        return False
    @property
    def underflow(self) -> bool:
        if len(self.keys) < self.header.min_keys and not self.is_root:
            return True
        if len(self.keys) < 1 and self.is_root:
            return True
        return False
    @property
    def full(self): return len(self.keys) == self.header.max_keys
    @property
    def has_spare_keys(self): return len(self.keys) > self.header.min_keys

    def set_dirty(func):
        def wrapper(self, *args, **kwargs):
            ret = func(self,*args, **kwargs)
            self.dirty = True
            return ret
        return wrapper

    def __init__(self, header: PageHeader, data: List):
        self.header = header
        self.dirty = False
        if self.header.type == PageType.LEAF:
            self.pointers = []
            self.keys = data[::2]
            self.records = data[1::2]


        elif self.header.type == PageType.INTERNAL:
            self.records = []
            self.pointers = data[::2]
            self.keys = data[1::2]

        else:
            self.records = []
            self.pointers = []
            self.keys = []

    @set_dirty # type: ignore
    def free(self, next_page_id: int):
        self.header = PageHeader(type=PageType.FREE, id=self.header.id, parent=next_page_id)
        self.keys.clear()
        self.pointers.clear()
        self.records.clear()

    def find_index(self, key: int) -> int:
        #binary search left
        low: int  = 0
        high : int = len(self.keys)
        while low < high:
            m = (low + high) // 2
            if  key > self.keys[m]:
                low = m + 1
            else:
                high = m
        return low

    def key_exist(self, idx: int, key: int) -> bool:
        n = len(self.keys)
        if idx >= n: return False
        if self.keys[idx] == key: return True
        return False

    def search(self, key) -> Record | int:
        idx = self.find_index(key)
        if self.header.type == PageType.LEAF:
            if not self.key_exist(idx, key):
                raise ValueError(f"Key: {key} doesn't exist in the tree")
            return self.records[idx]
        elif self.header.type == PageType.INTERNAL:
            return self.pointers[idx]
        else:
            raise ValueError("Free pages cannot be searched")

    @set_dirty # type: ignore
    def insert(self, pos: int,  key: int, data: Record | int):
        if self.header.type == PageType.INTERNAL:
            self.pointers.insert(pos, data)
            self.keys.insert(pos, key)
        elif self.header.type == PageType.LEAF:
            if self.key_exist(pos, key):
                raise ValueError(f"Key: {key} already exist in the tree")
            self.keys.insert(pos, key)
            self.records.insert(pos, data)
        else:
            raise ValueError("Cannot insert into Free Pages")

    @set_dirty # type: ignore
    def delete(self, pos: int, key: int = -1) -> Record | None:
        if self.header.type == PageType.INTERNAL:
            # if not self.key_exist(pos, key):
            #     raise ValueError(f"Key: {key} dont exist in the tree node")
            self.keys.pop(pos)
            self.pointers.pop(pos)
            return None
        elif self.header.type == PageType.LEAF:
            if not self.key_exist(pos, key):
                raise ValueError(f"Key: {key} dont exist in the tree leaf")
            self.keys.pop(pos)
            rec = self.records.pop(pos)
            return rec
        else:
            raise ValueError("Cannot insert into Free Pages")

    @set_dirty # type: ignore
    def update_rec(self, key: int, rec: Record):
        if not self.is_leaf:
            raise ValueError("Only leafs pages can be updated")
        idx = self.find_index(key)
        if not self.key_exist(idx, key):
            raise ValueError(f"Key: {key} dont exist in the tree")
        self.records[idx] = rec

    def __bytes__(self):
        self.header.key_count = len(self.keys)
        if self.header.key_count > self.header.max_keys:
            raise RuntimeError(f"Page f{self.header.id} Compromised  "
                               f"key count {self.header.key_count}"
                               f"larger than max_keys {self.header.max_keys}")
        if self.header.type == PageType.LEAF:
            assert len(self.records) == len(self.keys)
        elif self.header.type == PageType.INTERNAL and len(self.pointers)>0 :
            assert len(self.pointers) == len(self.keys) + 1

        buf = bytearray()
        buf += bytes(self.header)

        data_frm: str
        if self.header.type == PageType.LEAF:
            data_frm = f"<{self.LEAF_FMT * self.header.key_count}"

            flat_data = []
            for key, rec in zip(self.keys, self.records):
                flat_data.extend((key, *astuple(rec)))

            buf += struct.pack(data_frm, *flat_data)

        elif self.header.type == PageType.INTERNAL:
            data_frm = "<" + ((self.PTR_FMT + self.KEY_FMT) * self.header.key_count) + self.PTR_FMT

            flat_data = []
            for ptr, key in zip(self.pointers, self.keys):
                flat_data.extend((ptr, key))

            flat_data.append(self.pointers[-1])
            buf += struct.pack(data_frm, *flat_data)

        elif self.header.type == PageType.FREE: pass

        return bytes(buf)

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Page | None":
        header: PageHeader = PageHeader.from_bytes(raw)
        data = []
        offset = header.BYTES_SIZE

        if header.type == PageType.LEAF:
            for _ in range(header.key_count):
                key = struct.unpack_from(("<"+cls.KEY_FMT), raw, offset)[0]
                offset += struct.calcsize(cls.KEY_FMT)

                rec = Record.from_bytes(raw, offset)
                offset += Record.BYTES_SIZE
                data.extend((key, rec))

        elif header.type == PageType.INTERNAL:
            for _ in range(header.key_count):
                ptr, key = struct.unpack_from(("<"+cls.PTR_FMT+cls.KEY_FMT), raw, offset)
                offset += struct.calcsize((cls.PTR_FMT+cls.KEY_FMT))

                data.extend((ptr, key))
            ptr = struct.unpack_from("<"+cls.PTR_FMT, raw, offset)[0]
            offset += struct.calcsize(cls.PTR_FMT)
            data.append(ptr)

        elif header.type == PageType.FREE: data = []

        return cls(header, data)

    @property
    def view_no_rec(self):
        output: str = ""
        if self.header.type == PageType.LEAF:
            if self.is_root: output += f"RL{self.header.id}["
            else:output += f"L{self.header.id}["
            output += "|".join([f"k{key}" for key, rec in zip(self.keys, self.records)])
            output += "]"

        elif self.header.type == PageType.INTERNAL:
            if self.is_root: output += f"RN{self.header.id}["
            else: output += f"N{self.header.id}["
            output += "|".join(f"p{pointer}|k{key}" for pointer, key in zip(self.pointers, self.keys))
            output += f"|p{self.pointers[-1]}]"

        return output

    def __str__(self):
        output: str = ""
        if self.header.type == PageType.LEAF:
            if self.is_root: output += f"RL{self.header.id}["
            else: output += f"L{self.header.id}["

            output += "|".join([f"(k{key},{rec})" for key, rec in zip(self.keys, self.records)])
            output += "]"

        elif self.header.type == PageType.INTERNAL:
            if self.is_root: output += f"RN{self.header.id}["
            else: output += f"N{self.header.id}["
            output += "|".join(f"p{pointer}|k{key}" for pointer, key in zip(self.pointers, self.keys))
            output += f"|p{self.pointers[-1]}]"

        return output

    def __repr__(self):
        output = ""
        output += f"header=[{str(self.header)}],"
        output += "keys=[" + ",".join(str(key) for key in self.keys) + "],"
        output += "pointers=[" + ",".join(str(ptr) for ptr in self.pointers) + "],"
        output += "records=[" + ",".join(str(rec) for rec in self.records) + "],"

        flags = []
        if self.full: flags.append("full")
        if self.overflow: flags.append("overflow")
        if self.underflow: flags.append("underflow")
        if self.is_root: flags.append("root")
        if self.is_leaf: flags.append("leaf")
        if self.dirty: flags.append("dirty")
        status = ",".join(flags)
        output += f"status:[{flags}]"

        return output







