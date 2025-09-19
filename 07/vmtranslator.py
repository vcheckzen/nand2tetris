from pathlib import Path
import sys
from typing import Self

from codewriter import CodeWriter
from parser import CommandType, Parser


class VMTranslator:
    def __init__(self, vmProgFile: str) -> Self:
        vmProgFile = Path(vmProgFile)
        asmProgFile = vmProgFile.parent.joinpath(
            f'{vmProgFile.stem}.asm')

        self.parser = Parser(vmProgFile)
        self.codewriter = CodeWriter(asmProgFile)

    def translate(self) -> None:
        while self.parser.hasMoreLines():
            self.parser.advance()
            self.codewriter.f.write(f'// {self.parser.curCmd()}\n')
            if self.parser.commandType() == CommandType.C_PUSH or self.parser.commandType() == CommandType.C_POP:
                self.codewriter.writePushPop(
                    self.parser.commandType(), self.parser.arg1(), self.parser.arg2())
            elif self.parser.commandType() == CommandType.C_ARITHMETIC:
                self.codewriter.writeArithmetic(self.parser.arg1())

        self.codewriter.writeInfiniteLoop()

    def finish(self) -> None:
        self.codewriter.close()
        self.parser.close()


if __name__ == '__main__':
    translator = VMTranslator(sys.argv[1])
    translator.translate()
    translator.finish()
