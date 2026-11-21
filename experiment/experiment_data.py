from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, List, Tuple, Annotated, Iterator
from pydantic import Field


class Experiment(ABC):
    # every iteration gives (d, r, records amount)
    @abstractmethod
    def iterations(self) -> Iterator[Tuple[int, int, int]]:
        pass


@dataclass()
class ExperimentRecords(Experiment):
    DATA_TYPE = int
    TYPE_NAME = "experiment_degrees"
    name: str
    operation_amount: Annotated[int, Field(ge=0)]
    leaf_degree: Annotated[int, Field(ge=1)]
    node_degree: Annotated[int, Field(ge=1)]
    data: List[DATA_TYPE]

    DEFAULT: ClassVar['ExperimentRecords']

    def __post_init__(self):
        self.data.sort()
        if self.operation_amount > self.data[0]:
            raise ValueError("Operations amount per type must be smaller or equal to maximum of records_amount")

    def iterations(self) -> Iterator[Tuple[int, int, int]]:
        for N in self.data:
            yield self.node_degree, self.leaf_degree, N

ExperimentRecords.DEFAULT = ExperimentRecords(
    name="default",
    operation_amount=500, leaf_degree=4, node_degree=4,
    data=[1000,2000,4000,8000,16000,32000,64000]
)


@dataclass()
class ExperimentDegrees(Experiment):
    DATA_TYPE = Tuple[int, int]
    TYPE_NAME = "experiment_degrees"
    name: str
    operation_amount: Annotated[int, Field(ge=0)]
    rec_amount: Annotated[int, Field(ge=10)]
    data: List[DATA_TYPE]

    DEFAULT: ClassVar['ExperimentDegrees']
    REVERSE_DEFAULT: ClassVar['ExperimentDegrees']

    def __post_init__(self):
        self.data.sort(key=lambda deg: sum(deg))
        if self.operation_amount > self.rec_amount:
            raise ValueError("Operations amount per type must be smaller or equal to records_amount")

    def iterations(self) -> Iterator[Tuple[int, int, int]]:
        for d, r in self.data:
            yield d, r, self.rec_amount


ExperimentDegrees.REVERSE_DEFAULT = ExperimentDegrees(
    name="reverse",
    operation_amount=1000, rec_amount=10000,
    data=[(4,2),(8,2),(8,4),(8,8),(16,4),(16,8),(16,16),
          (32,8),(32,16),(32,32),(64,16),(64,32),(64,64)]
)
ExperimentDegrees.DEFAULT = ExperimentDegrees(
    name="=default",
    operation_amount=1000, rec_amount=10000,
    data=[(2,4),(2,8),(4,8),(8,8),(4,16),(8,16),(16,16),
          (8,32),(16,32),(32,32),(16,64),(32,64),(64,64)]
)