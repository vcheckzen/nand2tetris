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
WrapperFuncName = 'Sys._wrapper'


class CodeWriter:
    def __init__(self, output_file: Path, bootstrap: bool = False) -> Self:
        self.f = output_file.open(mode='w', encoding="utf-8")
        self.setFile(output_file.stem)
        self.setFunc(WrapperFuncName)

        if bootstrap:
            self.f.write(f"""\
@256
D=A
@SP
M=D
""")
            self.writeCall('Sys.init', 0)

    def setFile(self, fileName: str) -> None:
        self.vmName = fileName

    def setFunc(self, funcName: str) -> None:
        self.funcName = funcName
        self.cmpLabelNum = -1
        self.retLabelNum = -1

    def innerFuncLabel(self, label: str) -> None:
        return f'{self.funcName}${label}'

    def nextCmpLabel(self, op: str) -> tuple[str, str]:
        self.cmpLabelNum += 1
        prefix = f'{self.funcName}$cmp.{self.cmpLabelNum}'
        return f'{prefix}.{op}', f'{prefix}.NOT.{op}'

    def nextRetLabel(self) -> str:
        self.retLabelNum += 1
        return f'{self.funcName}$ret.{self.retLabelNum}'

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

    def assign(self, src: int | str, dst: str) -> None:
        self.writeD(src)
        self.saveD(dst)

    def pushFromVar(self, src: str) -> None:
        self.writeD(src)
        self.pushFromD()

    def popToVar(self, dst: str) -> None:
        self.popToD()
        self.saveD(dst)

    def selectSegment(self, segment: str, index: int) -> None:
        addr = BaseAddressLocation[segment]
        if isinstance(addr, type(lambda x: x)):
            self.f.write(f"""\
@{addr(self.vmName, index)}
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
        trueLabel, falseLabel = self.nextCmpLabel(asmOp)
        self.f.write(f"""\
@{trueLabel}
D;J{asmOp}
@SP
A=M-1
M=0
@{falseLabel}
0;JMP
({trueLabel})
@SP
A=M-1
M=-1
({falseLabel})
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

    def writeLabel(self, label: str) -> None:
        self.f.write(f'({self.innerFuncLabel(label)})\n')

    def writeGoto(self, label: str) -> None:
        self.f.write(f"""\
@{self.innerFuncLabel(label)}
0;JMP
""")

    def writeIf(self, label: str) -> None:
        self.popToD()
        self.f.write(f"""\
@{self.innerFuncLabel(label)}
D;JNE
""")

    def writeFunction(self, functionName: str, nVars: int) -> None:
        self.setFunc(functionName)

        self.f.write(f"({functionName})\n")
        if nVars:
            self.writeD(0)
            for _ in range(nVars):
                self.pushFromD()

    def writeCall(self, functionName: str, nArgs: int) -> None:
        retAddr = self.nextRetLabel()
        self.f.write(f"""\
@{retAddr}
D=A
""")
        self.pushFromD()
        self.pushFromVar('LCL')
        self.pushFromVar('ARG')
        self.pushFromVar('THIS')
        self.pushFromVar('THAT')
        self.f.write(f"""\
@SP
D=M
@LCL
M=D
@5
D=D-A
@{nArgs}
D=D-A
@ARG
M=D
@{functionName}
0;JMP
({retAddr})
""")

    def writeReturn(self) -> None:
        # The textbook's approach
        #         self.f.write(f"""\
        # // frame = LCL
        # @LCL
        # D=M
        # @R13
        # M=D
        # // retAddr = *(frame-5)
        # @5
        # A=D-A
        # D=M
        # @R14
        # M=D
        # // *ARG = pop()
        # """)
        #         self.popToD()
        #         self.f.write(f"""\
        # @ARG
        # A=M
        # M=D
        # // SP = ARG+1
        # D=A+1
        # @SP
        # M=D
        # // THAT = *(frame-1)
        # @R13
        # A=M-1
        # D=M
        # @THAT
        # M=D
        # // THIS = *(frame-2)
        # @R13
        # D=M
        # @2
        # A=D-A
        # D=M
        # @THIS
        # M=D
        # // ARG = *(frame-3)
        # @R13
        # D=M
        # @3
        # A=D-A
        # D=M
        # @ARG
        # M=D
        # // LCL = *(frame-4)
        # @R13
        # D=M
        # @4
        # A=D-A
        # D=M
        # @LCL
        # M=D
        # // goto retAddr
        # @R14
        # A=M
        # 0;JMP
        # """)

        # Personal approach
        # Save ret val, not writing to *ARG directly, cause the caller's ret addr can be overwritten
        self.popToVar(TempVariable.R13)
        # Save the pos of ARG, cause it will restore to the caller's
        self.assign('ARG', TempVariable.R14)
        # Let SP be align to LCL
        self.assign('LCL', 'SP')
        # Restore the caller's frame
        self.popToVar('THAT')
        self.popToVar('THIS')
        self.popToVar('ARG')
        self.popToVar('LCL')
        # The caller's ret addr
        self.popToVar(TempVariable.R15)
        # Restore SP
        self.writeD(TempVariable.R14)
        self.f.write(f"""\
@SP
M=D+1
""")
        # Write ret val to *ARG and jump to the caller
        self.writeD(TempVariable.R13)
        self.f.write(f"""\
@R14
A=M
M=D
@R15
A=M
0;JMP
""")

    def writeInfiniteLoop(self) -> None:
        self.setFunc(WrapperFuncName)
        self.f.write(f"""\
({self.innerFuncLabel('END')})
@{self.innerFuncLabel('END')}
0;JMP
""")

    def close(self) -> None:
        self.f.close()
