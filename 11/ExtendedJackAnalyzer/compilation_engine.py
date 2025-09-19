from io import TextIOWrapper
from typing import Self, Tuple

from jack_tokenizer import JackTokenizer, TkType
from symbol_table import Kind, SymbolTable, VarKind, Variable

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
        self.clsSymTbl = SymbolTable()
        self.subRtSymTbl = SymbolTable()
        self.clsSymTbl.reset()
        self.clsName = None
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

    def lookupSymbol(self, name: str) -> Variable | None:
        if name in self.subRtSymTbl:
            return self.subRtSymTbl[name]
        if name in self.clsSymTbl:
            return self.clsSymTbl[name]
        return None

    def writeIdentifier(self, category: Kind, type: str = None,  declaring: bool = True, forward: bool = True, usePrv: bool = False, isMethod: bool = False):
        k, v = self.peek(2, prv=usePrv)

        if category == Kind.NONE:
            var = self.lookupSymbol(v)
            if var != None:
                category = var.kind
        elif category == Kind.CLASS and declaring:
            self.clsName = v
        elif category == Kind.SUBROUTINE and declaring:
            self.subRtSymTbl.reset()
            if isMethod:
                self.subRtSymTbl.define('this', self.clsName, Kind.ARG)

        self.writeTag(k.value)
        self.f.write(f"<name> {v} </name>\n")
        self.f.write(f"<category> {category.value} </category>\n")

        if category in VarKind:
            if category == Kind.STATIC or category == Kind.FIELD:
                if v not in self.clsSymTbl:
                    self.clsSymTbl.define(v, type, category)
                idx = self.clsSymTbl.indexOf(v)
            else:
                if v not in self.subRtSymTbl:
                    self.subRtSymTbl.define(v, type, category)
                idx = self.subRtSymTbl.indexOf(v)
            self.f.write(f"<index> {idx} </index>\n")

        usage = 'declared' if declaring else 'used'
        self.f.write(f"<usage> {usage} </usage>\n")
        self.writeTag(k.value, end=True)

        if forward:
            self.advance()

    # write kv except whose key is a identifier
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
        # self.writeKV()
        self.writeIdentifier(Kind.CLASS)
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
        kind = Kind[self.peek().upper()]
        self.writeKV()
        # type: 'int' | 'char' | 'boolean' | className: identifier
        type = self.peek()
        if self.peek(0) == TkType.IDENTIFIER:
            self.writeIdentifier(Kind.CLASS, declaring=False)
        else:
            self.writeKV()
        # varName: identifier
        # self.writeKV()
        self.writeIdentifier(kind, type)
        # (',' varName)* ';'
        while True:
            if self.peek() == ';':
                self.writeKV()
                break
            # ','
            self.writeKV()
            # varName
            # self.writeKV()
            self.writeIdentifier(kind, type)
        self.writeTag("classVarDec", end=True)

    def compileSubroutine(self) -> None:
        self.writeTag("subroutineDec")
        # ('constructor' | 'function' | 'method')
        isMethod = self.peek() == 'method'
        self.writeKV()
        # ('void' | type)
        # type: 'int' | 'char' | 'boolean' | className: identifier
        # self.writeKV()
        if self.peek(0) == TkType.IDENTIFIER:
            self.writeIdentifier(Kind.CLASS, declaring=False)
        else:
            self.writeKV()
        # subroutineName
        # self.writeKV()
        self.writeIdentifier(Kind.SUBROUTINE, isMethod=isMethod)
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
            # type: 'int' | 'char' | 'boolean' | className: identifier
            type = self.peek()
            # self.writeKV()
            if self.peek(0) == TkType.IDENTIFIER:
                self.writeIdentifier(Kind.CLASS, declaring=False)
            else:
                self.writeKV()
            # self.writeKV()
            self.writeIdentifier(Kind.ARG, type)
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
        # type: 'int' | 'char' | 'boolean' | className: identifier
        # self.writeKV()
        type = self.peek()
        if self.peek(0) == TkType.IDENTIFIER:
            self.writeIdentifier(Kind.CLASS, declaring=False)
        else:
            self.writeKV()

        # varName
        # self.writeKV()
        self.writeIdentifier(Kind.VAR, type)
        # (',' varName)*
        while True:
            if self.peek() != ',':
                break
            # ','
            self.writeKV()
            # varName
            # self.writeKV()
            self.writeIdentifier(Kind.VAR, type)
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
        # self.writeKV()
        # let writeIdentifier determine what kind the var belonging to
        self.writeIdentifier(Kind.NONE, declaring=False)
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
            # self.writeKV()
            var = self.lookupSymbol(self.peek())
            if var != None:
                # varName
                self.writeIdentifier(var.kind, var.type, declaring=False)
            else:
                # className or subroutineName
                self.advance()
                if self.peek() == ".":
                    # className
                    self.writeIdentifier(
                        Kind.CLASS, declaring=False, forward=False, usePrv=True)
                else:
                    # subroutineName
                    self.writeIdentifier(
                        Kind.SUBROUTINE, declaring=False, forward=False, usePrv=True)

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
                    # self.writeKV()
                    self.writeIdentifier(Kind.SUBROUTINE, declaring=False)
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
        if self.peek(0) != TkType.SYMBOL or self.peek() != ')':
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
