from enum import StrEnum
from pathlib import Path
from typing import Self

from parser import CommandType


class TempVariable(StrEnum):
    R13 = "R13"
    R14 = "R14"
    R15 = "R15"


UnaryOperator = {
    'neg': '-',
    'not': '!'
}
BinaryOperator = {
    'add': '+',
    'sub': '-',
    'and': '&',
    'or': '|'
}
CompareOperator = {
    'eq', 'gt', 'lt'
}
BaseAddressLocation = {
    'argument': 'ARG',
    'local': 'LCL',
    'this': 'THIS',
    'that': 'THAT',
    'pointer': 3,
    'temp': 5,
    'static': lambda fname, i: f'{fname}.{i}'
}


class CodeWriter:
    def __init__(self, output_file: Path) -> Self:
        self.f = output_file.open(mode='w', encoding='utf-8')
        self.fname = output_file.stem
        self.label_num = -1

    def nextLabelPrefix(self) -> str:
        self.label_num += 1
        return f'{self.fname}.L.{self.label_num}'

    def pushFromD(self) -> None:
        """
        stack[SP++] = D
        """
        self.f.write("""\
@SP
M=M+1
A=M-1
M=D
""")

    def popToD(self) -> None:
        """
        D = stack[--SP]
        """
        self.f.write("""\
@SP
AM=M-1
D=M
""")

    def saveD(self, dst: str) -> None:
        self.f.write(f"""\
@{dst}
M=D
""")

    def writeD(self, src: int | str) -> None:
        self.f.write(f"""\
@{src}
D={"A" if isinstance(src, int) else "M"}
""")

    def selectSegment(self, segment: str, index: int) -> None:
        addr = BaseAddressLocation[segment]
        if isinstance(addr, type(lambda x: x)):
            self.f.write(f"""\
@{addr(self.fname, index)}
D=A
""")
        else:
            if isinstance(addr, int):
                self.writeD(addr)
            else:
                self.f.write(f"""\
@{addr}
D=M
""")
            self.f.write(f"""\
@{index}
AD=D+A
""")

    def pushFromSegment(self, segment: str, index: int) -> None:
        if segment == 'constant':
            self.writeD(index)
        else:
            self.selectSegment(segment, index)
            self.f.write(f"D=M\n")
        self.pushFromD()

    def popToSegment(self, segment: str, index: int) -> None:
        """
        occupy R13
        """
        self.selectSegment(segment, index)
        self.saveD(TempVariable.R13)
        self.popToD()
        self.f.write("""\
@R13
A=M
M=D
""")

    def writeUnaryArithmetic(self, asmOp: str) -> None:
        self.f.write(f"""\
@SP
A=M-1
M={asmOp}M
""")

    def writeBinary(self, asmOp: str) -> None:
        self.f.write(f"""\
@SP
M=M-1
A=M-1
D=M
A=A+1
D=D{asmOp}M
""")

    def writeBinaryArithmetic(self, asmOp: str) -> None:
        self.writeBinary(asmOp)
        self.f.write("""\
A=A-1
M=D
""")

    def writeCompare(self, asmOp: str) -> None:
        self.writeBinary(BinaryOperator['sub'])
        label = f'{self.nextLabelPrefix()}.CMP.{asmOp}'
        self.f.write(f"""\
@{label}.TRUE
D;J{asmOp}
@SP
A=M-1
M=0
@{label}.END
0;JMP
({label}.TRUE)
@SP
A=M-1
M=-1
({label}.END)
""")

    def writeArithmetic(self, command: str) -> None:
        if command in UnaryOperator:
            self.writeUnaryArithmetic(UnaryOperator[command])
        elif command in BinaryOperator:
            self.writeBinaryArithmetic(BinaryOperator[command])
        else:
            self.writeCompare(command.upper())

    def writePushPop(self, command: CommandType, segment: str, index: int) -> None:
        if command == CommandType.C_PUSH:
            self.pushFromSegment(segment, index)
        else:
            self.popToSegment(segment, index)

    def writeInfiniteLoop(self) -> None:
        self.f.write("""\
(END)
@END
0;JMP
""")

    def close(self) -> None:
        self.f.close()
