from dataclasses import dataclass


@dataclass(slots=True)
class Metrics:
    i: int = 0
    o: int = 0
    page_count: int = 0
    def reset(self):
        self.i = self.o = self.page_count = 0