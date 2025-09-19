from enum import Enum
import os
from pathlib import Path
from typing import Self


class CommandType(Enum):
    C_ARITHMETIC = 1
    C_PUSH = 2
    C_POP = 3
    C_LABEL = 4
    C_GOTO = 5
    C_IF = 6
    C_FUNCTION = 7
    C_RETURN = 8
    C_CALL = 9


class Parser:
    def __init__(self, input_file: Path) -> Self:
        self.f = input_file.open()
        self.cur_cmd = None

    def curCmd(self) -> str:
        return ' '.join(self.cur_cmd)

    def hasMoreLines(self) -> bool:
        cur_pos = self.f.tell()
        next_line = self.f.readline()
        self.f.seek(cur_pos)
        return bool(next_line)

    def advance(self) -> None:
        while True:
            line = self.f.readline()
            slash = line.rfind('//')
            if slash != -1:
                line = line[:slash]
            line = line.strip()
            if len(line) > 0 and not line.startswith('//'):
                self.cur_cmd = [part.strip() for part in line.split(' ')]
                break

    def commandType(self) -> CommandType:
        if self.cur_cmd[0] == 'push':
            return CommandType.C_PUSH
        if self.cur_cmd[0] == 'pop':
            return CommandType.C_POP
        if self.cur_cmd[0] == 'label':
            return CommandType.C_LABEL
        if self.cur_cmd[0] == 'goto':
            return CommandType.C_GOTO
        if self.cur_cmd[0] == 'if-goto':
            return CommandType.C_IF
        if self.cur_cmd[0] == 'function':
            return CommandType.C_FUNCTION
        if self.cur_cmd[0] == 'call':
            return CommandType.C_CALL
        if self.cur_cmd[0] == 'return':
            return CommandType.C_RETURN
        return CommandType.C_ARITHMETIC

    def arg1(self) -> str:
        if len(self.cur_cmd) == 1:
            return self.cur_cmd[0]
        return self.cur_cmd[1]

    def arg2(self) -> int:
        return int(self.cur_cmd[2])

    def close(self) -> None:
        self.f.close()
