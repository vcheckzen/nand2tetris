from typing import Self, Tuple

from jack_tokenizer import JackTokenizer, KyWd, TkType
from symbol_table import Kind, SymbolTable, Variable
from vm_writer import ArithmeticCommand, Segment, VMWriter


ValueMapTable = {
    TkType.KEYWORD: JackTokenizer.keyword,
    TkType.SYMBOL: JackTokenizer.symbol,
    TkType.IDENTIFIER: JackTokenizer.identifier,
    TkType.INT_CONST: JackTokenizer.intVal,
    TkType.STRING_CONST: JackTokenizer.stringVal
}
VarKindSegmentTable = {
    Kind.STATIC: Segment.STATIC,
    Kind.FIELD: Segment.THIS,
    Kind.ARG: Segment.ARGUMENT,
    Kind.VAR: Segment.LOCAL
}
BinaryOp = {'+', '-', '*', '/', '&', '|', '<', '>', '='}
UnaryOp = {'-', '~'}
KeywordConst = {KyWd.TRUE, KyWd.FALSE, KyWd.NULL, KyWd.THIS}
BinaryOpArithmeticCommandTable = {
    '+': ArithmeticCommand.ADD,
    '-': ArithmeticCommand.SUB,
    '&': ArithmeticCommand.AND,
    '|': ArithmeticCommand.OR,
    '<': ArithmeticCommand.LT,
    '>': ArithmeticCommand.GT,
    '=': ArithmeticCommand.EQ
}


class CompilationEngine:
    def __init__(self, tkNzr: JackTokenizer, vmWriter: VMWriter) -> Self:
        self.tkNzr = tkNzr
        self.vmWriter = vmWriter
        self.prvKV: Tuple[TkType, int | str] = None
        self.curKV: Tuple[TkType, int | str] = None
        self.labelIndex = 0
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

    def peek(self, i: int = 1, prv: bool = False, toStr: bool = False) -> Tuple[TkType, KyWd | int | str] | TkType | KyWd | int | str:
        kv = self.prvKV if prv else self.curKV
        if 0 <= i <= 1:
            return str(kv[i]) if toStr else kv[i]
        return kv

    def atSymbol(self, s: str, prv: bool = False) -> None:
        k, v = self.peek(2, prv=prv)
        return k == TkType.SYMBOL and v == s

    def lookupSymbol(self, name: str) -> Variable | None:
        if name in self.rtSymTbl:
            return self.rtSymTbl[name]
        if name in self.clsSymTbl:
            return self.clsSymTbl[name]
        return None

    def addSymbol(self,  kind: Kind, type: str, usePrv=False, forward=True) -> None:
        if kind == Kind.STATIC or kind == Kind.FIELD:
            tb = self.clsSymTbl
        else:
            tb = self.rtSymTbl

        tb.define(self.peek(prv=usePrv, toStr=True), type, kind)

        if forward:
            self.advance()

    def nextLabel(self, prefix: str) -> str:
        self.labelIndex += 1
        return f"{prefix}{self.labelIndex}"

    def compileClass(self) -> None:
        self.clsSymTbl = SymbolTable()
        self.clsSymTbl.reset()
        self.rtSymTbl = SymbolTable()

        # 'class'
        self.advance()
        # className
        self.className = self.peek()
        self.advance()
        # '{'
        self.advance()
        # classVarDec* subroutineDec*
        while True:
            v = self.peek()
            if v in [KyWd.STATIC, KyWd.FIELD]:
                self.compileClassVarDec()
            elif v in [KyWd.CONSTRUCTOR, KyWd.FUNCTION, KyWd.METHOD]:
                self.compileSubroutine()
            else:
                break
        # '}'
        self.advance()

    def compileClassVarDec(self) -> None:
        # ('static' | 'field')
        kind = Kind[self.peek(toStr=True).upper()]
        self.advance()
        # type: 'int' | 'char' | 'boolean' | className: identifier
        type = self.peek(toStr=True)
        self.advance()
        # varName: identifier
        self.addSymbol(kind, type)
        # (',' varName)* ';'
        while True:
            if self.atSymbol(';'):
                self.advance()
                break
            # ','
            self.advance()
            # varName
            self.addSymbol(kind, type)

    def compileSubroutine(self) -> None:
        self.rtSymTbl.reset()

        # ('constructor' | 'function' | 'method')
        self.subroutineType = self.peek()
        if self.subroutineType == KyWd.METHOD:
            self.rtSymTbl.define('this', self.className, Kind.ARG)
        self.advance()

        # ('void' | type)
        # type: 'int' | 'char' | 'boolean' | className: identifier
        self.advance()
        # subroutineName
        self.subroutineName = self.peek()
        self.advance()
        # '('
        self.advance()
        # parameterList
        self.compileParameterList()
        # ')
        self.advance()
        # subroutineBody
        self.compileSubroutineBody()

    def compileParameterList(self) -> None:
        # ((type varName) (',' type VarName)*)?
        while not self.atSymbol(')'):
            # (type varName)
            # type: 'int' | 'char' | 'boolean' | className: identifier
            type = self.peek(toStr=True)
            self.advance()
            # varName
            self.addSymbol(Kind.ARG, type)
            if self.atSymbol(','):
                # ','
                self.advance()

    def compileSubroutineBody(self) -> None:
        # '{'
        self.advance()

        # varDec*
        while self.peek() == KyWd.VAR:
            self.compileVarDec()

        self.vmWriter.writeFunction(
            f"{self.className}.{self.subroutineName}", self.rtSymTbl.varCount(Kind.VAR))

        if self.subroutineType == KyWd.METHOD:
            self.vmWriter.writePush(Segment.ARGUMENT, 0)
            self.vmWriter.writePop(Segment.POINTER, 0)
        elif self.subroutineType == KyWd.CONSTRUCTOR:
            self.vmWriter.writePush(
                Segment.CONSTANT, self.clsSymTbl.varCount(Kind.FIELD))
            self.vmWriter.writeCall('Memory.alloc', 1)
            self.vmWriter.writePop(Segment.POINTER, 0)

        # statements
        self.compileStatements()
        # '}'
        self.advance()

    def compileVarDec(self) -> None:
        # 'var'
        self.advance()
        # type: 'int' | 'char' | 'boolean' | className: identifier
        type = self.peek(toStr=True)
        self.advance()
        # varName
        self.addSymbol(Kind.VAR, type)
        # (',' varName)*
        while self.atSymbol(','):
            # ','
            self.advance()
            # varName
            self.addSymbol(Kind.VAR, type)
        # ';'
        self.advance()

    def compileStatements(self) -> None:
        while True:
            v = self.peek()
            if v == KyWd.LET:
                self.compileLet()
            elif v == KyWd.IF:
                self.compileIf()
            elif v == KyWd.WHILE:
                self.compileWhile()
            elif v == KyWd.DO:
                self.compileDo()
            elif v == KyWd.RETURN:
                self.compileReturn()
            else:
                break

    def compileLet(self) -> None:
        # 'let'
        self.advance()
        # varName
        varName = self.peek()
        var = self.lookupSymbol(varName)
        self.advance()
        isArray = False
        if self.atSymbol('['):
            isArray = True
            self.vmWriter.writePush(VarKindSegmentTable[var.kind], var.index)
            # '['
            self.advance()
            # expression
            self.compileExpression()
            # ']'
            self.advance()
            self.vmWriter.writeArithmetic(ArithmeticCommand.ADD)
        # '='
        self.advance()
        # expression
        self.compileExpression()
        # ';'
        self.advance()
        if isArray:
            self.vmWriter.writePop(Segment.TEMP, 0)
            self.vmWriter.writePop(Segment.POINTER, 1)
            self.vmWriter.writePush(Segment.TEMP, 0)
            self.vmWriter.writePop(Segment.THAT, 0)
        else:
            self.vmWriter.writePop(VarKindSegmentTable[var.kind], var.index)

    def compileIf(self) -> None:
        # 'if'
        self.advance()
        # '('
        self.advance()
        # expression
        self.compileExpression()
        # ')'
        self.advance()
        self.vmWriter.writeArithmetic(ArithmeticCommand.NOT)
        elseLabel = self.nextLabel("ELSE")
        self.vmWriter.writeIf(elseLabel)
        # '{'
        self.advance()
        # statements
        self.compileStatements()
        # '}'
        endIfLabel = self.nextLabel("ENDIF")
        self.vmWriter.writeGoto(endIfLabel)
        self.vmWriter.writeLabel(elseLabel)
        self.advance()
        if self.peek() == KyWd.ELSE:
            # 'else'
            self.advance()
            # '{'
            self.advance()
            # statements
            self.compileStatements()
            # '}'
            self.advance()
        self.vmWriter.writeLabel(endIfLabel)

    def compileWhile(self) -> None:
        loopLabel = self.nextLabel("LOOP")
        self.vmWriter.writeLabel(loopLabel)
        # 'while'
        self.advance()
        # '('
        self.advance()
        # expression
        self.compileExpression()
        # ')'
        self.advance()
        self.vmWriter.writeArithmetic(ArithmeticCommand.NOT)
        endLoopLabel = self.nextLabel("ENDLOOP")
        self.vmWriter.writeIf(endLoopLabel)
        # '{'
        self.advance()
        # statements
        self.compileStatements()
        # '}'
        self.advance()
        self.vmWriter.writeGoto(loopLabel)
        self.vmWriter.writeLabel(endLoopLabel)

    def compileDo(self) -> None:
        # 'do'
        self.advance()
        # subroutineCall
        self.compileTerm()
        self.vmWriter.writePop(Segment.TEMP, 0)
        # ';'
        self.advance()

    def compileReturn(self) -> None:
        # 'return'
        self.advance()
        if self.atSymbol(';'):
            self.vmWriter.writePush(Segment.CONSTANT, 0)
        else:
            # expression?
            self.compileExpression()
        # ';'
        self.advance()
        self.vmWriter.writeReturn()

    def compileExpression(self) -> None:
        self.compileTerm()
        while self.peek(0) == TkType.SYMBOL and self.peek() in BinaryOp:
            # op
            op = self.peek()
            self.advance()
            self.compileTerm()
            if op == '*':
                self.vmWriter.writeCall('Math.multiply', 2)
            elif op == '/':
                self.vmWriter.writeCall('Math.divide', 2)
            else:
                self.vmWriter.writeArithmetic(
                    BinaryOpArithmeticCommandTable[op])

    def compileTerm(self) -> None:
        # integerConstant | stringConstant | keywordConstant | varName |
        # varName '[' expression ']' | '(' expression ')' | (unaryOp term) | subroutineCall
        k, v = self.peek(2)
        if k == TkType.INT_CONST:
            self.vmWriter.writePush(Segment.CONSTANT, v)
            self.advance()
        elif k == TkType.STRING_CONST:
            self.vmWriter.writePush(Segment.CONSTANT, len(v))
            self.vmWriter.writeCall("String.new", 1)
            for c in v:
                self.vmWriter.writePush(Segment.CONSTANT, ord(c))
                self.vmWriter.writeCall("String.appendChar", 2)
            self.advance()
        elif v in KeywordConst:
            if v == KyWd.NULL or v == KyWd.FALSE:
                self.vmWriter.writePush(Segment.CONSTANT, 0)
            elif v == KyWd.TRUE:
                self.vmWriter.writePush(Segment.CONSTANT, 1)
                self.vmWriter.writeArithmetic(ArithmeticCommand.NEG)
            elif v == KyWd.THIS:
                self.vmWriter.writePush(Segment.POINTER, 0)
            self.advance()
        elif k == TkType.SYMBOL and v in UnaryOp:
            self.advance()
            self.compileTerm()
            if v == '-':
                self.vmWriter.writeArithmetic(ArithmeticCommand.NEG)
            elif v == '~':
                self.vmWriter.writeArithmetic(ArithmeticCommand.NOT)
        elif k == TkType.SYMBOL and v == '(':
            self.advance()
            self.compileExpression()
            self.advance()
        else:
            # varName | varName '[' expression ']' | subroutineCall
            # subroutineCall:
            # subroutineName '(' expressionList ')' |
            # (className | varName) '.' subroutineName '(' expressionList ')'

            # varName | subroutineName | (className | varName)
            # 1. varName -> token after it
            # 2. varName '[' expression ']' -> '['
            # 3. subroutineCall
            #   3.1. subroutineName '(' expressionList ')' -> '('
            #   3.2. (className | varName) '.' subroutineName '(' expressionList ')' -> '.'
            self.advance()
            if self.atSymbol('['):
                name = self.peek(prv=True)
                var = self.lookupSymbol(name)
                self.vmWriter.writePush(
                    VarKindSegmentTable[var.kind], var.index)
                # '['
                self.advance()
                # expression
                self.compileExpression()
                # ']'
                self.advance()
                self.vmWriter.writeArithmetic(ArithmeticCommand.ADD)
                self.vmWriter.writePop(Segment.POINTER, 1)
                self.vmWriter.writePush(Segment.THAT, 0)
            else:
                isMethod = True
                subroutineName = None
                if self.atSymbol('.'):
                    name = self.peek(prv=True)
                    var = self.lookupSymbol(name)
                    if var == None:
                        # function or constructor call
                        isMethod = False
                        className = name
                    else:
                        # method call on other object
                        className = var.type
                        self.vmWriter.writePush(
                            VarKindSegmentTable[var.kind], var.index)

                    # '.'
                    self.advance()
                    # subroutineName
                    subroutineName = self.peek()
                    self.advance()

                if self.atSymbol('('):
                    if not subroutineName:
                        # method call on this object
                        className = self.className
                        subroutineName = self.peek(prv=True)
                        self.vmWriter.writePush(Segment.POINTER, 0)

                    # '('
                    self.advance()
                    # expressionList
                    nArgs = self.compileExpressionList()
                    # ')'
                    self.advance()

                    if isMethod:
                        nArgs += 1

                    self.vmWriter.writeCall(
                        f"{className}.{subroutineName}", nArgs)
                else:
                    # varName
                    name = self.peek(prv=True)
                    var = self.lookupSymbol(name)
                    if var != None:
                        self.vmWriter.writePush(
                            VarKindSegmentTable[var.kind], var.index)

    def compileExpressionList(self) -> int:
        # (expression (',' expression)* )?
        cnt = 0
        if not self.atSymbol(')'):
            cnt += 1
            self.compileExpression()
            while self.atSymbol(','):
                # ','
                self.advance()
                cnt += 1
                self.compileExpression()
        return cnt
