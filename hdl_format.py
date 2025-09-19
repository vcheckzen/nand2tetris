import re
import pathlib


def format_hdl_parts_section(text):
    # 捕获 PARTS 段
    def parts_replacer(match):
        lines = match.group(1).splitlines()
        formatted = []

        for line in lines:
            # 保留缩进
            indent = re.match(r'\s*', line).group(0)
            # 忽略空行
            if not line.strip():
                formatted.append(line)
                continue
            # 移除行尾注释临时存储
            code, *comment = line.split('//', 1)
            # 格式化每个 key=value 对
            code = re.sub(r'\s*=\s*', '=', code)
            # 清理多余空格
            code = re.sub(r'\s*,\s*', ', ', code.strip())
            line_fmt = indent + code
            if comment:
                line_fmt += ' // ' + comment[0].strip()
            formatted.append(line_fmt)

        return 'PARTS:\n' + '\n'.join(formatted) + '\n}'

    # 应用 PARTS 段格式化
    return re.sub(r'PARTS:\n((?:.*\n)*?)\}', parts_replacer, text)


def format_hdl_file(file: pathlib.Path):
    original = file.read_text()
    updated = format_hdl_parts_section(original)
    if original != updated:
        print(f'Formatted: {file}')
        file.write_text(updated)


# 递归格式化所有 .hdl 文件
for file in pathlib.Path('.').rglob('*.hdl'):
    if file.suffix == '.hdl':
        format_hdl_file(file)
