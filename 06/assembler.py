import sys
from os import SEEK_SET
from pathlib import Path

from symboltable import SymbolTable
from parser import Parser, A_INSTRUCTION, L_INSTRUCTION
import codegen


class Assembler:
    def __init__(self, sourceFilePath):
        sourceFilePath = Path(sourceFilePath).resolve()
        workingPath = sourceFilePath.parent
        destFilePath = workingPath.joinpath(f'{sourceFilePath.stem}.hack')

        symbols = SymbolTable()
        for i in range(16):
            symbols.addEntry(f'R{i}', i)
        symbols.addEntry('SP', 0)
        symbols.addEntry('LCL', 1)
        symbols.addEntry('ARG', 2)
        symbols.addEntry('THIS', 3)
        symbols.addEntry('THAT', 4)
        symbols.addEntry('SCREEN', 16384)
        symbols.addEntry('KBD', 24576)

        # Phase 1
        src = sourceFilePath.open()
        parser = Parser(src)
        linenumber = -1
        while parser.hasMoreLines():
            parser.advance()
            if parser.instructionType() == L_INSTRUCTION:
                symbols.addEntry(parser.symbol(), linenumber + 1)
            else:
                linenumber += 1

        # Phase 2
        src.seek(0, SEEK_SET)
        dest = destFilePath.open(mode='w', encoding='utf-8')

        parser = Parser(src)
        fieldTable = [
            (parser.comp, codegen.comp),
            (parser.dest, codegen.dest),
            (parser.jump, codegen.jump),
        ]

        firstLine = True
        nextAvailableAddress = 16
        while parser.hasMoreLines():
            parser.advance()
            if parser.instructionType() == L_INSTRUCTION:
                continue

            if not firstLine:
                dest.write('\n')
            firstLine = False

            if parser.instructionType() == A_INSTRUCTION:
                if not parser.symbol().isdecimal():
                    if not symbols.contains(parser.symbol()):
                        symbols.addEntry(parser.symbol(), nextAvailableAddress)
                        nextAvailableAddress += 1
                    address = symbols.getAddress(parser.symbol())
                else:
                    address = int(parser.symbol())
                machineCode = f'{address:0{16}b}'
            else:
                machineCode = '111'
                for parse, gen in fieldTable:
                    machineCode += gen(parse())
            dest.write(f'{machineCode}')

        dest.close()
        src.close()


if __name__ == '__main__':
    Assembler(sys.argv[1])
