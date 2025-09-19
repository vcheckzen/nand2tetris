def dest(mnemonic):
    bin = ['0', '0', '0']
    if mnemonic != "null":
        dst = 'ADM'
        for d in mnemonic:
            bin[dst.find(d)] = '1'
    return ''.join(bin)


def comp(mnemonic):
    compTable = {
        '0':   '0101010',
        '1':   '0111111',
        '-1':  '0111010',
        'D':   '0001100',
        'A':   '0110000',
        'M':   '1110000',
        '!D':  '0001101',
        '!A':  '0110001',
        '!M':  '1110001',
        '-D':  '0001111',
        '-A':  '0110011',
        '-M':  '1110011',
        'D+1': '0011111',
        'A+1': '0110111',
        'M+1': '1110111',
        'D-1': '0001110',
        'A-1': '0110010',
        'M-1': '1110010',
        'D+A': '0000010',
        'D+M': '1000010',
        'D-A': '0010011',
        'D-M': '1010011',
        'A-D': '0000111',
        'M-D': '1000111',
        'D&A': '0000000',
        'D&M': '1000000',
        'D|A': '0010101',
        'D|M': '1010101'
    }
    return compTable[mnemonic]


def jump(mnemonic):
    if mnemonic == 'null':
        return '000'
    if mnemonic == 'JGT':
        return '001'
    if mnemonic == 'JEQ':
        return '010'
    if mnemonic == 'JGE':
        return '011'
    if mnemonic == 'JLT':
        return '100'
    if mnemonic == 'JNE':
        return '101'
    if mnemonic == 'JLE':
        return '110'
    if mnemonic == 'JMP':
        return '111'
