import sys
from jack_analyzer import JackAnalyzer

if __name__ == "__main__":
    JackAnalyzer(sys.argv[1], tokenizeOnly=len(sys.argv) == 2)
