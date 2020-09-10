from functools import partial
from random import randint, randrange, sample
from timeit import timeit
import sys
from utils import Bits


class BenchmarkBitsExtract:

    def __init__(self, set_size):
        self.test_set = self.generate_args(set_size)

    def generate_args(self, n):
        result = []
        for i in range(n):
            operand = randrange(0, 2**16)
            arg = ''.join((str(item)*randint(1, 8) for item in sample((*range(9), '-'), k=4)))
            result.append((operand, arg))
        self.test_set = result
        return result

    def show_args(self):
        print(*(f'{bin(item[0]).ljust(18)} {item[1]}' for item in self.test_set), sep='\n')

    def run_benchmark(self, method):
        method = getattr(Bits, method)
        for operand, mask in self.test_set:
            method(Bits(operand), mask)

    def run(self):
        print(f"Running benchmark for extract() and .extract2() with {len(self.test_set)} calls")
        results = [
            timeit(partial(self.run_benchmark, 'extract'), number=1),
            timeit(partial(self.run_benchmark, 'extract2'), number=1),
        ]
        print(f"Bits.extract  = {results[0]}")
        print(f"Bits.extract2 = {results[1]}")


if __name__ == '__main__':

    benchmarks = {
        'extract': BenchmarkBitsExtract(10000),
    }

    if len(sys.argv) == 1:
        benchmark = benchmarks.popitem()[1]
    else:
        bench_id = sys.argv[1]
        benchmark = benchmarks.get(bench_id, None)
        if benchmark is None:
            print(f"Error: invalid benchmark id: {bench_id}")

    benchmark.run()
