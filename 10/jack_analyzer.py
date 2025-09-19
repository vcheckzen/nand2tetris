from pathlib import Path
from typing import Self

from jack_tokenizer import JackTokenizer
from compilation_engine import EscapeTable, ValueMapTable, CompilationEngine


class JackAnalyzer:
    def __init__(self, src: str | Path, tokenizeOnly: bool = False) -> Self:
        if isinstance(src, str):
            src = Path(src)
        self.tokenizeOnly = tokenizeOnly

        if src.is_file():
            self.wd = src.parent
            self.od = self.wd.joinpath("build")
            self.od.mkdir(exist_ok=True)
            self.analyzeFile(src)
        else:
            self.wd = src
            self.od = self.wd.joinpath("build")
            self.od.mkdir(exist_ok=True)
            for root, _, files in self.wd.walk():
                for f in files:
                    if f.endswith(".jack"):
                        self.analyzeFile(Path(root).joinpath(f))

    def analyzeFile(self, src: Path) -> None:
        if self.tokenizeOnly:
            self.tokenize(src)
        else:
            self.compile(src)

    def tokenize(self, src: Path) -> None:
        dst = self.od.joinpath(f"{src.stem}T.xml")
        sf = src.open(mode="r", encoding="utf-8")
        df = dst.open(mode="w", encoding="utf-8")
        
        tn = JackTokenizer(sf)
        df.write("<tokens>\n")
        while tn.hasMoreTokens():
            tn.advance()
            k = tn.tokenType().value
            v = ValueMapTable[tn.tokenType()](tn)
            if v in EscapeTable:
                v = EscapeTable[v]
            df.write(f"<{k}> {v} </{k}>\n")
        df.write("</tokens>\n")

        df.close()
        sf.close()

    def compile(self, src: Path) -> None:
        dst = self.od.joinpath(f"{src.stem}.xml")
        sf = src.open(mode="r", encoding="utf-8")
        df = dst.open(mode="w", encoding="utf-8")

        eg = CompilationEngine(JackTokenizer(sf), df)
        eg.compileClass()

        df.close()
        sf.close()
