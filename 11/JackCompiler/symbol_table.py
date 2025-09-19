from enum import StrEnum
from typing import Dict, Self


class Kind(StrEnum):
    STATIC = "static"
    FIELD = "field"
    ARG = "arg"
    VAR = "var"
    CLASS = "class"
    SUBROUTINE = "subroutine"
    NONE = "none"


VarKind = {Kind.STATIC, Kind.FIELD, Kind.ARG, Kind.VAR}


class Variable:
    def __init__(self, name: str, type: str, kind: Kind, index: int):
        self.name = name
        self.type = type
        self.kind = kind
        self.index = index


class SymbolTable:
    def __init__(self) -> Self:
        self.index: Dict[str, int] = dict()
        self.table: Dict[str, Variable] = dict()

    def __contains__(self, key):
        return key in self.table

    def __getitem__(self, key):
        return self.table[key]

    def reset(self) -> None:
        self.table.clear()
        for k in VarKind:
            self.index[k] = 0

    def define(self, name: str, type: str, kind: Kind) -> None:
        self.table[name] = Variable(name, type, kind, self.varCount(kind))
        self.index[kind] = self.varCount(kind) + 1

    def varCount(self, kind: Kind) -> int:
        return self.index[kind]

    def kindOf(self, name: str) -> Kind:
        if name in self.table:
            return self.table[name].kind
        return Kind.NONE

    def typeOf(self, name: str) -> str:
        return self.table[name].type

    def indexOf(self, name: str) -> int:
        return self.table[name].index
