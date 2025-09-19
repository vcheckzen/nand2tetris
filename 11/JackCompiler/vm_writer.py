from enum import StrEnum
from io import TextIOWrapper
from typing import Self


class Segment(StrEnum):
    CONSTANT = "constant"
    ARGUMENT = "argument"
    LOCAL = "local"
    STATIC = "static"
    THIS = "this"
    THAT = "that"
    POINTER = "pointer"
    TEMP = "temp"


class ArithmeticCommand(StrEnum):
    ADD = "add"
    SUB = "sub"
    NEG = "neg"
    EQ = "eq"
    GT = "gt"
    LT = "lt"
    AND = "and"
    OR = "or"
    NOT = "not"


class VMWriter:
    def __init__(self, output: TextIOWrapper) -> Self:
        self.f = output

    def write(self, cmd: str) -> None:
        self.f.write(cmd + "\n")

    def writePush(self, segment: Segment, index: int) -> None:
        self.write(f"push {segment} {index}")

    def writePop(self, segment: Segment, index: int) -> None:
        self.write(f"pop {segment} {index}")

    def writeArithmetic(self, command: ArithmeticCommand) -> None:
        self.write(command)

    def writeLabel(self, label: str) -> None:
        self.write(f"label {label}")

    def writeGoto(self, label: str) -> None:
        self.write(f"goto {label}")

    def writeIf(self, label: str) -> None:
        self.write(f"if-goto {label}")

    def writeCall(self, name: str, nArgs: int) -> None:
        self.write(f"call {name} {nArgs}")

    def writeFunction(self, name: str, nVars: int) -> None:
        self.write(f"function {name} {nVars}")

    def writeReturn(self) -> None:
        self.write("return")

    def close(self) -> None:
        self.f.close()
