from jack_compiler import JackCompiler

if __name__ == "__main__":
    folders = [
        "../Seven",
        "../ConvertToBin",
        "../Square",
        "../Average",
        "../Pong",
        "../ComplexArrays",
        "../Tetris"
    ]
    for fd in folders:
        JackCompiler(fd)
