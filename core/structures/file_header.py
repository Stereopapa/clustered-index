import struct
from dataclasses import dataclass, field
from typing import ClassVar

@dataclass(slots=True)
class FileHeader:
    page_size: int
    magic: bytes = b"B+Tr"
    root_page_id: int = 1
    free_pages_head: int = 0


    dirty: bool = field(default=False, init=False)

    FMT: ClassVar[str] = "I4sII"

    def __bytes__(self):
        out = bytearray()
        data = struct.pack(
            self.FMT,
            self.page_size, self.magic, self.root_page_id, self.free_pages_head
        )
        padding = b"\x00" * (self.page_size - struct.calcsize(self.FMT))
        out += data
        out += padding
        return bytes(out)

    @classmethod
    def from_bytes(cls, raw: bytes):
        unpacked = struct.unpack_from(cls.FMT, raw, 0)
        return cls(unpacked[0], unpacked[1], unpacked[2], unpacked[3])