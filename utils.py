from typing import List
from random import Random



def pow_range(*args, factor: int = 2):
    start: int = 0
    end: int = 0
    if len(args) == 1:
        end = args[0]
    elif len(args) == 2:
        start = args[0]
        end = args[1]
    else: raise TypeError(f"pow_range expected max 3 arguments go {len(args)}")

    curr = start
    while curr < end:
        yield curr
        curr *= factor