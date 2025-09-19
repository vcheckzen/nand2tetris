# usage:
#   test tokenizer: python test.py
#   test all: python test.py compile
import shutil
import subprocess
from pathlib import Path
import sys

from jack_analyzer import JackAnalyzer

cmp_tool = Path("../toolkit/tools/TextComparer.bat")


def compare(cmp: Path, gen: Path) -> None:
    try:
        # Run the batch file and capture its output
        # `capture_output=True` captures stdout and stderr
        # `text=True` decodes the output as text using default encoding (usually UTF-8)
        # `check=True` raises a CalledProcessError if the command returns a non-zero exit code
        result = subprocess.run(
            map(str, [cmp_tool, cmp, gen]), capture_output=True, text=True, check=True, shell=True)

        # Print the standard output
        print("Standard Output:")
        print(result.stdout)

        # Print the standard error (if any)
        if result.stderr:
            print("\nStandard Error:")
            print(result.stderr)

    except subprocess.CalledProcessError as e:
        print(f"Error running batch script: {e}")
        print(f"Return Code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error Output: {e.stderr}")
    except FileNotFoundError:
        print(f"Error: Batch file not found at {cmp_tool}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    testTokenizerOnly = len(sys.argv) == 1
    suffix = ".xml"
    if testTokenizerOnly:
        suffix = "T.xml"

    print("Single file test:")
    single = [
        "Square/Main.jack",
        "Square/Square.jack",
        "Square/SquareGame.jack",
        "ExpressionLessSquare/Main.jack",
        "ExpressionLessSquare/Square.jack",
        "ExpressionLessSquare/SquareGame.jack",
        "ArrayTest/Main.jack"
    ]

    for f in single:
        bp = Path(f).parent.joinpath("build")
        if bp.exists():
            shutil.rmtree(bp)

        JackAnalyzer(f, tokenizeOnly=testTokenizerOnly)
        f = Path(f)
        cmp = f.parent.joinpath(f"{f.stem}{suffix}")
        gen = bp.joinpath(f"{f.stem}{suffix}")
        compare(cmp, gen)

    print("Folder test:")
    folder = [
        "Square",
        "ExpressionLessSquare",
        "ArrayTest"
    ]
    for p in folder:
        bp = Path(p).joinpath("build")
        if bp.exists():
            shutil.rmtree(bp)

        JackAnalyzer(p, tokenizeOnly=testTokenizerOnly)
        p = Path(p)
        for root, dirs, files in p.walk():
            for f in files:
                if f.endswith(".jack"):
                    f = Path(root).joinpath(f)
                    cmp = f.parent.joinpath(f"{f.stem}{suffix}")
                    gen = bp.joinpath(f"{f.stem}{suffix}")
                    compare(cmp, gen)
