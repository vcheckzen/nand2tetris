# usage:
#   test single file: python test.py
#   test folder: python test.py folder
import re
import sys
import shutil
import subprocess
import xml.dom.minidom
from pathlib import Path

from jack_analyzer import JackAnalyzer


def get_git_diff_blocks(file1, file2) -> int:
    # 运行git diff命令
    result = subprocess.run([
        'git', 'diff', '--numstat',
        file1, file2
    ], capture_output=True, text=True)
    # 计算hunk数量
    return int(result.stdout.split()[1])


def compare_xml_identifiers(file1: str, file2: str) -> None:
    def format(path: str) -> str:
        dom = xml.dom.minidom.parse(path)
        pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")

        if isinstance(pretty_xml, bytes):
            pretty_xml = pretty_xml.decode('utf-8')

        # # 修复空标签
        pretty_xml = re.sub(r'(\s*)<(\w+)>\s+</\2>', lambda match: f"{match.group(1)}<{match.group(2)}>\n{match.group(1)}</{match.group(2)}>",
                            string=pretty_xml, flags=re.MULTILINE | re.DOTALL)

        # 修复空行
        pretty_xml = '\n'.join(
            [ln for ln in pretty_xml.split('\n') if ln.strip()])

        with open(path, mode="w", encoding="utf-8") as f:
            f.write(pretty_xml)

        return pretty_xml

    # --- format both files (overwrite them) ---
    formatted1 = format(file1)
    formatted2 = format(file2)

    # --- count </identifier> ---
    count1 = formatted1.count("</identifier>")
    count2 = formatted2.count("</identifier>")
    if count1 != count2:
        raise ValueError(f"Tag count mismatch: {count1} vs {count2}")

    # --- diff ---
    hunk_count = get_git_diff_blocks(file1, file2)

    if hunk_count != count1:
        print(
            f"{file1} and {file2}'s diff blocks number not equals to their identifier tags number")
        raise ValueError(
            f"Diff block count {hunk_count} != identifier count {count1}")

    print(f"Success: {count1} identifier tags, {hunk_count} diff blocks")


if __name__ == "__main__":
    compileSingleFile = len(sys.argv) == 1

    testTokenizerOnly = False
    suffix = ".xml"

    folder = [
        "Square",
        "ExpressionLessSquare",
        "ArrayTest"
    ]
    for p in folder:
        bp = Path(p).joinpath("build")
        if bp.exists():
            shutil.rmtree(bp)

    if compileSingleFile:
        print("Compile single file:")
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
            JackAnalyzer(f, tokenizeOnly=testTokenizerOnly)
            f = Path(f)
            bp = f.parent.joinpath("build")
            cmp = f.parent.joinpath(f"{f.stem}{suffix}")
            gen = bp.joinpath(f"{f.stem}{suffix}")
            compare_xml_identifiers(cmp.__str__(), gen.__str__())
    else:
        print("Compile folder:")
        for p in folder:
            JackAnalyzer(p, tokenizeOnly=testTokenizerOnly)

            p = Path(p)
            bp = p.joinpath("build")
            for root, dirs, files in p.walk():
                for f in files:
                    if f.endswith(".jack"):
                        f = Path(root).joinpath(f)
                        cmp = f.parent.joinpath(f"{f.stem}{suffix}")
                        gen = bp.joinpath(f"{f.stem}{suffix}")
                        compare_xml_identifiers(cmp.__str__(), gen.__str__())

    print("Now compare them on <identifier> tags manually")
