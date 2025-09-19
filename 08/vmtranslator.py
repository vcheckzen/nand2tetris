from pathlib import Path
import sys
from typing import Self

from codewriter import CodeWriter
from parser import CommandType, Parser


class VMTranslator:
    def __init__(self, vm: str, bootstrap: bool) -> Self:
        input = Path(vm)
        if input.is_file():
            output = input.parent.joinpath(f'{input.stem}.asm')
            self.coder = CodeWriter(output, bootstrap)
            self.parser = Parser(input)
            self.translate()
        else:
            output = input.joinpath(f'{input.stem}.asm')
            self.coder = CodeWriter(output, bootstrap)
            for parent, _, filenames in input.walk():
                for f in filenames:
                    if f.endswith('.vm'):
                        new_file = Path(parent).joinpath(f)
                        self.parser = Parser(new_file)
                        self.coder.setFile(new_file.stem)
                        self.translate()

        if not bootstrap:
            self.coder.writeInfiniteLoop()

        self.finish()

    def translate(self) -> None:
        parser, coder = self.parser, self.coder
        while parser.hasMoreLines():
            parser.advance()
            coder.f.write(f'// {parser.curCmd()}\n')
            cmd = parser.commandType()
            if cmd == CommandType.C_PUSH or cmd == CommandType.C_POP:
                coder.writePushPop(cmd, parser.arg1(), parser.arg2())
            elif cmd == CommandType.C_ARITHMETIC:
                coder.writeArithmetic(parser.arg1())
            elif cmd == CommandType.C_LABEL:
                coder.writeLabel(parser.arg1())
            elif cmd == CommandType.C_GOTO:
                coder.writeGoto(parser.arg1())
            elif cmd == CommandType.C_IF:
                coder.writeIf(parser.arg1())
            elif cmd == CommandType.C_FUNCTION:
                coder.writeFunction(parser.arg1(), parser.arg2())
            elif cmd == CommandType.C_CALL:
                coder.writeCall(parser.arg1(), parser.arg2())
            else:
                coder.writeReturn()

    def finish(self) -> None:
        self.coder.close()
        self.parser.close()


if __name__ == '__main__':
    VMTranslator(sys.argv[1], len(sys.argv) > 2)
