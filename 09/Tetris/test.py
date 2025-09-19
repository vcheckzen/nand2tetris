import os
from pathlib import Path

WD = Path(".")
JC = Path("../../toolkit/tools/JackCompiler.bat")
VME = Path("../../toolkit/tools/VMEmulator.bat")

for vm in WD.glob(WD / "*.vm"):
    vm.unlink()

os.system(f"{JC} . && {VME}")
