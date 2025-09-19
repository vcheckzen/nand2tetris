from collections import deque
from enum import StrEnum
from io import TextIOWrapper
from typing import Self


class TkType(StrEnum):
    KEYWORD = "keyword",
    SYMBOL = "symbol",
    IDENTIFIER = "identifier",
    INT_CONST = "integerConstant",
    STRING_CONST = "stringConstant"


class KyWd(StrEnum):
    CLASS = "class",
    METHOD = "method",
    FUNCTION = "function",
    CONSTRUCTOR = "constructor",
    INT = "int",
    BOOLEAN = "boolean",
    CHAR = "char",
    VOID = "void",
    VAR = "var",
    STATIC = "static",
    FIELD = "field",
    LET = "let",
    DO = "do",
    IF = "if",
    ELSE = "else",
    WHILE = "while",
    RETURN = "return",
    TRUE = "true",
    FALSE = "false",
    NULL = "null",
    THIS = "this"


Keyword = {k.value for k in KyWd}
Symbol = {'(', ')', '[', ']', '{', '}', ',', ';', '=',
          '.', '+', '-', '*', '/', '&', '|', '~', '<', '>'}


class JackTokenizer:
    def __init__(self, src: TextIOWrapper) -> Self:
        self.f = src
        self.buf = deque()
        self.lstChr = None
        self.tk = None
        self.ntk = None
        self.readUtilToken()

    def readLn(self) -> None:
        self.buf = deque(self.f.readline())

    def readChr(self) -> str:
        if len(self.buf) == 0:
            self.readLn()
            if len(self.buf) == 0:
                self.lstChr = None
                return ''
        self.lstChr = self.buf.popleft()
        return self.lstChr

    def backChr(self) -> None:
        if self.lstChr:
            self.buf.appendleft(self.lstChr)
            self.lstChr = None

    # return '' when EOF, or a str ending with chr first encountered
    def readUtil(self, chr) -> str:
        t = ''
        while True:
            c = self.readChr()
            # EOF
            if c == '':
                return ''
            t += c
            if c == chr:
                return t

    # return '' when EOF, or the first char not equaling to chr
    def readAll(self, chr) -> str:
        while True:
            c = self.readChr()
            # EOF or not chr
            if c != chr:
                return c

    # return '' when EOF, or the first char not equaling to \r, \n, \t and space
    def readAllEmpty(self) -> str:
        c = ' '
        while True:
            c = self.readAll(c)
            if c == '' or c not in "\r\n\t ":
                return c

    def readUtilToken(self) -> bool:
        # skip empty chars
        c = self.readAllEmpty()
        # EOF
        if c == '':
            return False

        # comment or division op
        if c == "/":
            c = self.readChr()
            # EOF
            if c == '':
                # file ending with '/' is invalid
                return False
            # skip line comment
            if c == "/":
                if self.readUtil('\n') == '':
                    return False
            # skip block comment
            elif c == '*':
                while True:
                    if self.readUtil('*') == '':
                        return False
                    if self.readChr() == '/':
                        break
            else:
                # division op
                self.backChr()
                self.ntk = "/"
                return True

            return self.readUtilToken()

        # read a symbol
        if c in Symbol:
            self.ntk = c
            return True

        # read a str const
        if c == '"':
            t = self.readUtil('"')
            # EOF
            if t == '':
                return False
            self.ntk = c + t
            return True

        # read a int const
        if c.isdigit():
            t = c
            while True:
                c = self.readChr()
                if not c.isdigit():
                    self.backChr()
                    self.ntk = t
                    return True
                t += c

        # keyword or identifier
        t = c
        while True:
            c = self.readChr()
            if not c.isalnum() and c != '_':
                self.backChr()
                self.ntk = t
                return True
            t += c

    def hasMoreTokens(self) -> bool:
        return self.ntk != None

    def advance(self) -> None:
        self.tk = self.ntk
        self.ntk = None
        self.readUtilToken()

    def tokenType(self) -> TkType:
        if self.tk in Keyword:
            return TkType.KEYWORD
        if self.tk in Symbol:
            return TkType.SYMBOL
        if self.tk[0] == '"':
            return TkType.STRING_CONST
        if self.tk[0].isdigit():
            return TkType.INT_CONST
        return TkType.IDENTIFIER

    def keyword(self) -> KyWd:
        for k in KyWd:
            if self.tk == k.value:
                return k

    def symbol(self) -> str:
        return self.tk

    def identifier(self) -> str:
        return self.tk

    def intVal(self) -> int:
        return int(self.tk)

    def stringVal(self) -> str:
        return self.tk[1:-1]
