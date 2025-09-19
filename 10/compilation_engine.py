from io import TextIOWrapper
from typing import Self, Tuple

from jack_tokenizer import JackTokenizer, TkType

EscapeTable = {
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    '&': "&amp;"
}
ValueMapTable = {
    TkType.KEYWORD: JackTokenizer.keyword,
    TkType.SYMBOL: JackTokenizer.symbol,
    TkType.IDENTIFIER: JackTokenizer.identifier,
    TkType.INT_CONST: JackTokenizer.intVal,
    TkType.STRING_CONST: JackTokenizer.stringVal
}

BinaryOp = {'+', '-', '*', '/', '&', '|', '<', '>', '='}
UnaryOp = {'-', '~'}
KeywordConst = {'true', 'false', 'null', 'this'}


class CompilationEngine:
    def __init__(self, tkNzr: JackTokenizer, output: TextIOWrapper) -> Self:
        self.tkNzr = tkNzr
        self.f = output
        self.prvKV: Tuple[TkType, int | str] = None
        self.curKV: Tuple[TkType, int | str] = None
        self.advance()

    def advance(self) -> None:
        self.prvKV = self.curKV
        if self.tkNzr.hasMoreTokens():
            self.tkNzr.advance()
            k = self.tkNzr.tokenType()
            v = ValueMapTable[k](self.tkNzr)
            self.curKV = k, v
        else:
            self.curKV = None

    def peek(self, i: int = 1, prv: bool = False) -> Tuple[TkType, int | str]:
        kv = self.curKV
        if prv:
            kv = self.prvKV
        if 0 <= i <= 1:
            return kv[i]
        return kv

    def writeTag(self, tag: str, end: bool = False) -> None:
        self.f.write(f"<{'/' if end else ''}{tag}>\n")

    def writeKV(self, forward: bool = True) -> None:
        k, v = self.curKV
        if v in EscapeTable:
            v = EscapeTable[v]
        self.f.write(f"<{k.value}>")
        self.f.write(f" {v} ")
        self.f.write(f"</{k.value}>\n")

        if forward:
            self.advance()

    def compileClass(self) -> None:
        self.writeTag("class")
        # 'class'
        self.writeKV()
        # className
        self.writeKV()
        # '{'
        self.writeKV()
        # classVarDec* subroutineDec*
        while True:
            v = self.peek()
            if v in ['static', 'field']:
                self.compileClassVarDec()
            elif v in ['constructor', 'function', 'method']:
                self.compileSubroutine()
            else:
                break
        # '}'
        self.writeKV()
        self.writeTag("class", end=True)

    def compileClassVarDec(self) -> None:
        self.writeTag("classVarDec")
        # ('static' | 'field')
        self.writeKV()
        # type: 'int' | 'char' | 'boolean' | className: identifier
        self.writeKV()
        # varName: identifier
        self.writeKV()
        # (',' varName)* ';'
        while True:
            self.writeKV()
            if self.peek(prv=True) == ';':
                break
            # varName
            self.writeKV()
        self.writeTag("classVarDec", end=True)

    def compileSubroutine(self) -> None:
        self.writeTag("subroutineDec")
        # ('constructor' | 'function' | 'method')
        self.writeKV()
        # ('void' | type)
        self.writeKV()
        # subroutineName
        self.writeKV()
        # '('
        self.writeKV()
        # parameterList
        self.compileParameterList()
        # ')
        self.writeKV()
        # subroutineBody
        self.compileSubroutineBody()
        self.writeTag("subroutineDec", end=True)

    def compileParameterList(self) -> None:
        self.writeTag("parameterList")
        # ((type varName) (',' type VarName)*)?
        while True:
            if self.peek() == ')':
                break
            # (type varName)
            self.writeKV()
            self.writeKV()
            if self.peek() == ')':
                break
            # ','
            self.writeKV()
        self.writeTag("parameterList", end=True)

    def compileSubroutineBody(self) -> None:
        self.writeTag("subroutineBody")
        # '{'
        self.writeKV()
        # varDec*
        while True:
            if self.peek() != 'var':
                break
            self.compileVarDec()
        # statements
        self.compileStatements()
        # '}'
        self.writeKV()
        self.writeTag("subroutineBody", end=True)

    def compileVarDec(self) -> None:
        self.writeTag("varDec")
        # 'var'
        self.writeKV()
        # 'type'
        self.writeKV()
        # varName
        self.writeKV()
        # (',' varName)*
        while True:
            if self.peek() != ',':
                break
            # ','
            self.writeKV()
            # varName
            self.writeKV()
        # ';'
        self.writeKV()
        self.writeTag("varDec", end=True)

    def compileStatements(self) -> None:
        self.writeTag("statements")
        while True:
            v = self.peek()
            if v == 'let':
                self.compileLet()
            elif v == 'if':
                self.compileIf()
            elif v == 'while':
                self.compileWhile()
            elif v == 'do':
                self.compileDo()
            elif v == 'return':
                self.compileReturn()
            else:
                break
        self.writeTag("statements", end=True)

    def compileLet(self) -> None:
        self.writeTag("letStatement")
        # 'let'
        self.writeKV()
        # varName
        self.writeKV()
        if self.peek() == '[':
            # '['
            self.writeKV()
            # expression
            self.compileExpression()
            # ']'
            self.writeKV()
        # '='
        self.writeKV()
        # expression
        self.compileExpression()
        # ';'
        self.writeKV()
        self.writeTag("letStatement", end=True)

    def compileIf(self) -> None:
        self.writeTag("ifStatement")
        # 'if'
        self.writeKV()
        # '('
        self.writeKV()
        # expression
        self.compileExpression()
        # ')'
        self.writeKV()
        # '{'
        self.writeKV()
        # statements
        self.compileStatements()
        # '}'
        self.writeKV()
        if self.peek() == 'else':
            # 'else'
            self.writeKV()
            # '{'
            self.writeKV()
            # statements
            self.compileStatements()
            # '}'
            self.writeKV()
        self.writeTag("ifStatement", end=True)

    def compileWhile(self) -> None:
        self.writeTag("whileStatement")
        # 'while'
        self.writeKV()
        # '('
        self.writeKV()
        # expression
        self.compileExpression()
        # ')'
        self.writeKV()
        # '{'
        self.writeKV()
        # statements
        self.compileStatements()
        # '}'
        self.writeKV()
        self.writeTag("whileStatement", end=True)

    def compileDo(self) -> None:
        self.writeTag("doStatement")
        # 'do'
        self.writeKV()
        # subroutineCall
        self.compileTerm(withTag=False)
        # ';'
        self.writeKV()
        self.writeTag("doStatement", end=True)

    def compileReturn(self) -> None:
        self.writeTag("returnStatement")
        # 'return'
        self.writeKV()
        # expression?
        if self.peek() != ';':
            self.compileExpression()
        # ';'
        self.writeKV()
        self.writeTag("returnStatement", end=True)

    def compileExpression(self) -> None:
        self.writeTag("expression")

        self.compileTerm()
        while True:
            if self.peek() not in BinaryOp:
                break
            # op
            self.writeKV()
            # term
            self.compileTerm()

        self.writeTag("expression", end=True)

    def compileTerm(self, withTag: bool = True) -> None:
        if withTag:
            self.writeTag("term")

        # integerConstant | stringConstant | keywordConstant | varName |
        # varName '[' expression ']' | '(' expression ')' | (unaryOp term) | subroutineCall
        k, v = self.peek(2)
        if k == TkType.INT_CONST:
            self.writeKV()
        elif k == TkType.STRING_CONST:
            self.writeKV()
        elif v in KeywordConst:
            self.writeKV()
        elif v in UnaryOp:
            self.writeKV()
            self.compileTerm()
        elif v == '(':
            self.writeKV()
            self.compileExpression()
            self.writeKV()
        else:
            # varName | varName '[' expression ']' | subroutineCall

            # subroutineCall:
            # subroutineName '(' expressionList ')' |
            # (className | varName) '.' subroutineName '(' expressionList ')'

            # varName | subroutineName | (className | varName)
            self.writeKV()

            v = self.peek()
            if v == '[':
                self.writeKV()
                self.compileExpression()
                self.writeKV()
            else:
                # varName | subroutineCall

                if v == '.':
                    # '.'
                    self.writeKV()
                    # subroutineName
                    self.writeKV()
                    v = self.peek()

                if v == '(':
                    # '('
                    self.writeKV()
                    # expressionList
                    self.compileExpressionList()
                    # ')'
                    self.writeKV()
                else:
                    # varName
                    pass
        if withTag:
            self.writeTag("term", end=True)

    def compileExpressionList(self) -> int:
        self.writeTag("expressionList")
        # (expression (',' expression)* )?
        cnt = 0
        if self.peek() != ')':
            cnt += 1
            self.compileExpression()
            while True:
                if self.peek() != ',':
                    break
                self.writeKV()
                cnt += 1
                self.compileExpression()
        self.writeTag("expressionList", end=True)
        return cnt
