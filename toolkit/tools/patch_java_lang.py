import os
import sys
import re

def patch_file(path, script_stem):
    # 跳过同名文件
    if os.path.splitext(os.path.basename(path))[0] == script_stem:
        return

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    changed = False
    new_lines = []

    for line in lines:
        # 忽略已经包含 -Duser.language 的
        if re.search(r'-Duser\.language\s*=', line):
            new_lines.append(line)
            continue

        # 替换 java 或 javaw 命令
        def repl(match):
            nonlocal changed
            changed = True
            return match.group(0) + ' -Duser.language=en -Duser.country=US '

        line = re.sub(r'(?<![\w-])(javaw?)(\s+)', repl, line, count=1)
        new_lines.append(line)

    if changed:
        backup = path + '.bak'
        os.rename(path, backup)
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"Patched: {path}")
    else:
        print(f"Skipped: {path}")

def main():
    script_name = os.path.basename(sys.argv[0])
    script_stem = os.path.splitext(script_name)[0]

    for root, _, files in os.walk('.'):
        for name in files:
            if name.endswith('.sh') or name.endswith('.bat'):
                patch_file(os.path.join(root, name), script_stem)

if __name__ == "__main__":
    main()
