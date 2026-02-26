import struct
from dataclasses import dataclass, astuple, fields
from typing import ClassVar
import random

@dataclass(slots=True)
class Record:
    mass: float
    velocity: float

    FMT: ClassVar[str] = "ff"
    BYTES_SIZE: ClassVar[int] = struct.calcsize(FMT)
    FLOAT_EPSILON : ClassVar[float] = 1e-6
    ARG_COUNT: ClassVar[int] = 2



    def __bytes__(self):
        return struct.pack(self.FMT, *astuple(self))

    @classmethod
    def from_bytes(cls, raw: bytes, offset: int) -> "Record":
        unpacked = struct.unpack_from(cls.FMT, raw, offset)
        return cls(unpacked[0], unpacked[1])

    @classmethod
    def random(cls):
        return cls(random.uniform(0, 100), random.uniform(0, 100))

    def __eq__(self, other):
        if not isinstance(other, Record):
            return NotImplemented
        return (
            abs(other.mass - self.mass) < self.FLOAT_EPSILON and
            abs(other.velocity - self.velocity) < self.FLOAT_EPSILON
        )

    def __str__(self):
        return f"m:{self.mass},v:{self.velocity}"
