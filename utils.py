from __future__ import annotations
from functools import reduce
from operator import or_, and_
from typing import Tuple

# TODO: short module description, purpose


class Bits(int):

    def set(self, *positions: int) -> Bits:
        """
        Set bits on specified 'positions' (set to 1)
        Position indexes start from zero and are counted from rightmost bit to the left
        >>> Bits(0b01).set(1) == Bits(0b11)
        >>> Bits(0b1010).set(0, 2) == Bits(0b1111)
        >>> Bits(0b0).set(3) == Bits(0b1000)
        """

        n = len(positions)
        if n == 1:
            return Bits(self | (1 << positions[0]))
        elif n > 1:
            return Bits(reduce(or_, (1 << bit for bit in positions), self))
        else:
            return self

    def clear(self, *positions: int) -> Bits:
        """
        Clear bits on specified 'positions' (set to 0)
        Position indexes start from zero and are counted from rightmost bit to the left
        >>> Bits(0b01).clear(0) == Bits(0b0)
        >>> Bits(0b1010).clear(3) == Bits(0b0010)
        >>> Bits(0b11).clear(0, 2) == Bits(0b10)
        """

        n = len(positions)
        if n == 1:
            return Bits(self & ~(1 << positions[0]))
        elif n > 1:
            return Bits(reduce(and_, (~(1 << bit) for bit in positions), self))
        else:
            return self

    def mask(self, mask: str) -> Bits:
        """
        Set/clear bits according to positions of 1 and 0 in 'mask' string
        1 sets the corresponding bit, 0 clears the bit, - (dash) leaves
            current bit unchanged (any character may be used instead of -)
        >>> Bits(0b0101).mask('-01-') == Bits(0b0011)
        >>> Bits(0b1100).mask('11') == Bits(0b1111)
        >>> Bits(0b1111).mask('-') == Bits(0b1111)
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
        >>> Bits(0b0100).flag(2) == True
        """
        return bool((self >> pos) & 0b1)

    def flags(self, n) -> Tuple[bool, ...]:
        """
        Convert 'n' rightmost bits to tuple of booleans
        Resulting order is right to left
        >>> Bits(0b0011).flags(3) == (True, True, False)
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
