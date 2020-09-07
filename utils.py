from __future__ import annotations
from functools import reduce
from operator import or_, and_
from typing import Tuple


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

    def mask(self, mask: str) -> Bits:
        """
        Set 0 and 1, leave - as is
        >>> Bits(0b0101).mask('-01-') == Bits(0b0011)
        """

        result = self
        for i, marker in enumerate(reversed(mask)):
            if marker == '1':
                result |= (1 << i)
            elif marker == '0':
                result &= ~(1 << i)
        return Bits(result)

    def flag(self, pos: int) -> bool:
        """
        Extract one-bit boolean from specified position
        """
        return bool((self >> pos) & 0b1)

    def flags(self, n) -> Tuple[bool, ...]:
        """
        Convert 'n' rightmost bits to tuple of booleans
        Resulting order is right to left
        """

        return tuple(bool((self >> i) & 0b1) for i in range(n))

    def place(self, what, pos):
        pass

    def extract(self, mask):
        # Mask may look like '8----2--'
        pass

    @staticmethod
    def compose():
        # former bitsarray()
        pass
