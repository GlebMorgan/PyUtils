from __future__ import annotations
from functools import reduce
from operator import or_, and_


class Bits(int):

    def set(self, *positions: int) -> Bits:
        n = len(positions)
        if n == 1:
            return Bits(self | (1 << positions[0]))
        elif n > 1:
            return Bits(reduce(or_, (1 << bit for bit in positions), self))
        else:
            return self

    def clear(self, *positions: int) -> Bits:
        n = len(positions)
        if n == 1:
            return Bits(self & ~(1 << positions[0]))
        elif n > 1:
            return Bits(reduce(and_, (~(1 << bit) for bit in positions), self))
        else:
            return self

    def mask(self, mask):
        """set 0 and 1, leave - as is"""

    def flag(self, pos):
        pass

    def flags(self, pos):
        pass

    def combine(self, *parts):
        pass

    def split(self, *margins):
        pass

    def extract(self, mask):
        pass