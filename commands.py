from abc import ABC, abstractmethod
from typing import List

from core.bplus_tree import BplusTree
from core.structures.record import Record


def validate_mass(mS: str) -> float:
    m =  float(mS)
    if m < 0.0:
        raise ValueError("Value Error: Mass should be positive number")
    return m

def validate_velocity(vS: str) -> float:
    v = float(vS)
    if v < 0.0:
        raise ValueError("Mass is positive number")
    return v

def validate_key(kS: str) -> int:
    k = int(kS)
    if k < 0.0:
       raise ValueError("Mass is positive number")
    return k

def validate_record(line: List) -> Record:
    if len(line) != Record.ARG_COUNT:
        raise ValueError("There should be only 2 arguments, Try again")
    m = validate_mass(line[0])
    v = validate_velocity(line[1])

    return Record(mass=m, velocity=v)


class Command(ABC):
    @abstractmethod
    def execute(self) -> str:
        pass


class SearchCommand(Command):
    def __init__(self, tree: BplusTree, args: List[str]):
        self.tree = tree
        self.key = validate_key(args[0])

    def execute(self) -> str:
        rec = self.tree.search(self.key)
        return f"Record with key {self.key} found {rec}"


class InsertCommand(Command):
    def __init__(self, tree: BplusTree, args: List[str]):
        self.tree = tree
        self.key = validate_key(args[0])
        self.rec = validate_record(args[1:])

    def execute(self) -> str:
        self.tree.insert(self.key, self.rec)
        return f"Inserted {self.rec} with key {self.key}"


class DeleteCommand(Command):
    def __init__(self, tree: BplusTree, args: List[str]):
        self.tree = tree
        self.key = validate_key(args[0])

    def execute(self) -> str:
        rec = self.tree.delete(self.key)
        return f"Deleted {rec} with {self.key} Deleted"


class UpdateCommand(Command):
    def __init__(self, tree: BplusTree, args: List[str]):
        self.tree = tree
        self.key = validate_key(args[0])
        self.new_key = validate_key(args[1])
        self.rec = validate_record(args[2:])

    def execute(self) -> str:
        self.tree.update(self.key, self.new_key, self.rec)
        return f"Updated {self.rec} with key {self.new_key}"
