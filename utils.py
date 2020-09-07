from functools import reduce
from operator import or_, and_


class Bits(int):
    def set(self, pos):
        if isinstance(pos, int):
            return self | (1 << pos)
        elif not isinstance(pos, str) and hasattr(pos, '__iter__'):
            return reduce(or_, (1 << bit for bit in pos), self)
        else:
            raise TypeError("Expected one or several bit position numbers")

    def clear(self, pos):
        if isinstance(pos, int):
            return self & ~(1 << pos)
        elif not isinstance(pos, str) and hasattr(pos, '__iter__'):
            return reduce(and_, (~(1 << bit) for bit in pos), self)
        else:
            raise TypeError("Expected one or several bit position numbers")

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