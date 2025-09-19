class SymbolTable:
    def __init__(self):
        self.tb = dict()

    def addEntry(self, symbol, address):
        self.tb[symbol] = address

    def contains(self, symbol):
        return symbol in self.tb

    def getAddress(self, symbol):
        return self.tb[symbol]
