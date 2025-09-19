import sys
from pathlib import Path
from typing import Self

from jack_tokenizer import JackTokenizer
from compilation_engine import CompilationEngine
from vm_writer import VMWriter


class JackCompiler:
    def __init__(self, src: str | Path) -> Self:
        if isinstance(src, str):
            src = Path(src)

        wd = src if src.is_dir() else src.parent
        self.od = wd.joinpath("build")
        self.od.mkdir(exist_ok=True)

        if src.is_file():
            self.compile(src)
        else:
            for root, _, files in src.walk():
                for f in files:
                    if f.endswith(".jack"):
                        self.compile(Path(root).joinpath(f))

    def compile(self, src: Path) -> None:
        dst = self.od.joinpath(f"{src.stem}.vm")
        sf = src.open(mode="r", encoding="utf-8")
        wt = VMWriter(dst.open(mode="w", encoding="utf-8"))

        eg = CompilationEngine(JackTokenizer(sf), wt)
        eg.compileClass()

        wt.close()
        sf.close()


if __name__ == "__main__":
    JackCompiler(sys.argv[1])
