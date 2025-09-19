import os


no_boot = [
    './ProgramFlow/BasicLoop/BasicLoop.vm',
    './ProgramFlow/FibonacciSeries/FibonacciSeries.vm',
    './FunctionCalls/SimpleFunction/SimpleFunction.vm'
]

boot = [
    './FunctionCalls/FibonacciElement',
    './FunctionCalls/NestedCall',
    './FunctionCalls/StaticsTest'
]

for f in no_boot:
    os.system(f'python vmtranslator.py {f}')

for f in boot:
    os.system(f'python vmtranslator.py {f} boot')
