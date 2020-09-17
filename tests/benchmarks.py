"""
Cmd script for comparing performances of two functions/methods
Script initializes specified `Benchmark` class with appropriate test data
    and runs both functions with identical sets of arguments
For list of options, run the script with -h option
"""

import sys
from abc import abstractmethod
from argparse import ArgumentParser
from functools import partial
from random import randint, randrange, sample
from timeit import timeit
from typing import Tuple, Callable, Sequence


class Benchmark:

    """
    Base class for preparing and running benchmarks
    Intended to be inherited and provided with appropriate test data sets
    `.generate_args()` need to be overridden to provide a set of argument lists
        for the pair of compared functions/methods (argument list may contain
        just one single element if function accepts a single argument)
    Lists of arguments are iterated over and acquired arguments are passed into target function
    In order to run a benchmark, instantiate required `Benchmark` and call its `.run()` method
    >>> benchmark = BenchmarkBytewise(10000, bytes_range=(200, 250), limit=10)
    >>> benchmark.run(times=3)
    """

    def __init__(self, dataset_size, functions, owner=None, **kwargs):
        self.owner: type = owner
        self.prefix = self.owner.__name__ + '.' if self.owner else ''
        if len(functions) != 2:
            raise ValueError("Can only compare 2 functions / methods")
        self.functions: Tuple[Callable, Callable] = functions
        self.names = tuple(f.__name__ for f in self.functions)
        self.kwargs: dict = kwargs
        print('Comparing functions {0}() and {1}() with kwargs ({2})'.format(
                *self.names, ', '.join(f'{k}={v}' for k, v in self.kwargs.items())
        ))
        self.data: Sequence = self.generate_args(dataset_size)

    @abstractmethod
    def generate_args(self, size) -> tuple:
        """
        Generate test data set of a benchmark
        Should return tuple of arguments / argument lists that would be passed to functions under benchmark
        Intended to be overridden in child classes
        """
        raise NotImplementedError

    @abstractmethod
    def show_args(self, n: int):
        """
        Show first `n` entries from test data set
        """
        raise NotImplementedError

    def benchmark(self, func):
        for args in self.data:
            func(*args, **self.kwargs)

    def run(self, times: int = 1):
        print(f"Running benchmark for {self.names[0]}() and {self.names[1]}() with {len(self.data)} calls")
        results = [timeit(partial(self.benchmark, f), number=times) for f in self.functions]

        faster, slower = sorted(results)
        winner = self.names[0] if faster == results[0] else self.names[1]

        ratio = (slower - faster) / faster
        difference = f'{ratio * 100:.4}%' if ratio < 1 else f'{ratio + 1:.3} times'

        print(f"{self.prefix}{self.names[0]}  = {results[0]}")
        print(f"{self.prefix}{self.names[1]} = {results[1]}")
        print(f"{self.prefix}{winner} is {difference} faster")


class BenchmarkBitsExtract(Benchmark):

    __id__ = 'extract'

    def __init__(self, dataset_size: int):
        from utils import Bits
        functions = Bits.extract, Bits.extract2
        super().__init__(dataset_size, functions, owner=Bits)

    def generate_args(self, n: int):
        print(f"Generating test data set: {n} items")
        result = []
        for i in range(n):
            operand = randrange(0, 2**16)
            arg = ''.join((str(item)*randint(1, 8) for item in sample((*range(9), '-'), k=4)))
            result.append((self.owner(operand), arg))
        return result

    def show_args(self, n: int):
        print(*(f'{bin(item[0]).ljust(18)} {item[1]}' for item in self.data[:n]), sep='\n')


class BenchmarkBytewise(Benchmark):

    __id__ = 'bytewise'

    def __init__(self, dataset_size: int, bytes_range: Tuple[int, int] = None, **kwargs):
        from utils import bytewise, bytewise2
        functions = bytewise, bytewise2
        self.range: Tuple[int, int] = bytes_range
        super().__init__(dataset_size, functions, **kwargs)

    def generate_args(self, n: int):
        print(f"Generating test data set: {n} items")
        gen_range = lambda: range(randint(*(self.range or (10, 255))))
        return tuple((bytes(randint(0, 255) for _ in gen_range()),) for _ in range(n))

    def show_args(self, n: int):
        print(*(f'{item.hex()} (len={len(item)})' for item in self.data[:n]), sep='\n')


if __name__ == '__main__':

    parser = ArgumentParser(description="Compare performance of two functions/methods")
    parser.add_argument('-b', '--benchmark', dest='bench', metavar='ID',
                        help="benchmark id to run (-l to list all available benchmarks)")
    parser.add_argument('-s', '--dataset-size', dest='size', metavar='SIZE', type=int, default=1000,
                        help="number of sets with different arguments for a benchmark run")
    parser.add_argument('-o', '--option', nargs='+', dest='options', metavar='OPT=VALUE', default=[],
                        help="additional options for Benchmark class or target function/method")
    parser.add_argument('-r', '--runs', type=int, default=1,
                        help="number of benchmark runs to average upon")
    parser.add_argument('-l', '--list', action='store_true',
                        help="list all available benchmark ids to use with -b")
    cmd = parser.parse_args()

    is_benchmark = lambda obj: getattr(obj, '__bases__', (None,))[0] is Benchmark
    benchmarks = {cls.__id__: cls for cls in locals().values() if is_benchmark(cls)}

    if cmd.list:
        print(*benchmarks.keys())
        sys.exit()

    if not cmd.bench:
        benchmark = BenchmarkBytewise(10000, bytes_range=(200, 250), limit=10)
        benchmark.run()

    else:
        options = {name: eval(value) for name, value in (spec.split('=') for spec in cmd.options)}
        benchmark = benchmarks.get(cmd.bench, None)
        if benchmark is None:
            raise ValueError(f"Invalid benchmark id: {cmd.bench} (use -l to list available ids)")

        benchmark(cmd.size, **options).run(cmd.runs)
