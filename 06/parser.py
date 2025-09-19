import os

A_INSTRUCTION = 0
C_INSTRUCTION = 1
L_INSTRUCTION = 2


class Parser:
    def __init__(self, file):
        self.f = file
        self.currentInstruction = None

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
                self.currentInstruction = line
                break

    def instructionType(self):
        if self.currentInstruction.startswith('@'):
            return A_INSTRUCTION
        if self.currentInstruction.startswith('('):
            return L_INSTRUCTION
        return C_INSTRUCTION

    def symbol(self):
        if self.instructionType() == A_INSTRUCTION:
            return self.currentInstruction[1:]
        return self.currentInstruction[1:-1]

    def dest(self):
        eqIndex = self.currentInstruction.find('=')
        if eqIndex < 0:
            return 'null'
        return self.currentInstruction[0:eqIndex]

    def comp(self):
        eqIndex = self.currentInstruction.find('=')
        semicolonIndex = self.currentInstruction.find(';')
        if semicolonIndex == -1:
            semicolonIndex = len(self.currentInstruction)
        return self.currentInstruction[eqIndex+1:semicolonIndex]

    def jump(self):
        semicolonIndex = self.currentInstruction.find(';')
        if semicolonIndex < 0:
            return 'null'
        return self.currentInstruction[semicolonIndex+1:]
