from __future__ import annotations

import re
from functools import reduce
from itertools import groupby
from operator import or_, and_
from typing import Tuple, List, Optional


# TODO: short module description, purpose


class Bits(int):
    """
    Wrapper around `int` treating a number as a bit sequence
    Provides a set of tools to manipulate, extract, insert, split, combine
        individual bits and bit sequences within a processed number
    All methods intended to modify the value in-place return a newly created `Bits` object
        since there's no way of manipulating underlying `int` value directly
    """

    def set(self, *positions: int) -> Bits:
        """
        Set bits on specified `positions` (set to `1`)
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
        Clear bits on specified `positions` (set to `0`)
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
        Set/clear bits according to positions of `1`s and `0`s in `mask` string
        Mask consists of 3 types of markers:
            • `1` – sets the the bit on corresponding position
            • `0` – clears the corresponding bit
            • `-` (dash) – leaves the corresponding bit unchanged
        Mask may use an arbitrary character distinct from `0` and `1`
            to denote position of a bit to be skipped
        Mask is right-aligned with processed number (to match least-significant bit)
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
        Extract one-bit boolean from specified position `pos`
        Position index starts from zero and is counted from rightmost bit to the left
        >>> Bits(0b0100).flag(2) == True
        """
        return bool((self >> pos) & 0b1)

    def flags(self, n: int) -> Tuple[bool, ...]:
        """
        Convert `n` rightmost bits to tuple of booleans
        Functionally is the inverse of `.compose()` method
        Resulting flags order conforms to default bit indexing - right to left
        >>> Bits(0b0100).flags(3) == (False, False, True)
        """
        return tuple(bool((self >> i) & 0b1) for i in range(n))

    @classmethod
    def compose(cls, *flags: bool) -> Bits:
        """
        Construct a `Bits` object out of given sequence of bits specified in `flags`
        Functionally is the inverse of `.flags()` method
        The bits placing order conforms to default bit indexing – right to left
        >>> Bits.compose(False, False, True, False) == Bits(0x100)
        """
        return Bits(reduce(or_, (bit << i for i, bit in enumerate(flags) if bit), Bits()))

    def extract(self, mask: str, *, sep: str = ' ') -> Tuple[int, ...]:
        """
        Pull out one or multiple values on sub-byte basis according to `mask`
        Mask consists of 3 types of markers:
            • *number marker* – digits 0..9
            • *delimiter* – any character (except for digit or specified separator character)
            • *separator* – character specified by `sep` (could not be another marker character)
        Each group of adjacent number markers holds position of a separate number to be extracted
            from current `Bits` object (represented as a bit sequence)
        The order of extraction is defined by value of marker digits themselves
        Multiple groups with the same digit would raise a `ValueError`
        Delimiter characters denote positions of the bits to be skipped (dash is recommended)
        Separator characters are intended to enhance readability and are simply ignored
        Mask is right-aligned with processed number (to match least-significant bit)
        >>> Bits(0b0001_1100).extract('111--') == (0b111,)
        >>> Bits(0b1100_0110).extract('2221 11-3') == (0b1, 0b110, 0b0)
        >>> Bits(0b0011_1010).extract('1122 2-13') -> ValueError  # duplicating marker group: 1
        """

        if sep:
            mask = ''.join(mask.split(sep))
        try:
            n = max(int(m) for m in mask if m.isdecimal())
        except ValueError:
            return ()
        result = [...] * (n + 1)
        pos = len(mask)
        for marker, group in groupby(mask):
            size = len(tuple(group))
            pos -= size
            if marker.isdecimal():
                i = int(marker)
                if result[i] is not Ellipsis:
                    raise ValueError(f"Duplicate mask marker group: {marker}")
                result[i] = self >> pos & (2 ** size - 1)
        return tuple(num for num in result if num is not Ellipsis)

    def extract2(self, mask: str, *, sep: str = ' ') -> List[int]:
        """
        A 20% slower implementation of `.extract()` with same functionality
        This variant also returns a `list` instead of a `tuple`
        """

        if sep:
            mask = ''.join(mask.split(sep))
        try:
            n = int(max(filter(str.isdecimal, mask)))
        except ValueError:
            return []
        result = []
        for marker in ''.join(map(str, range(n+1))):
            if marker in mask:
                before, group, *after = re.split(rf'({marker}+)', mask)
                if len(after) > 1:
                    raise ValueError(f"Duplicate mask marker group: {marker}")
                result.append(self >> len(after[0]) & (2 ** len(group) - 1))
        return result

    def pack(self, mask: str, *nums: int, sep: str = ' ') -> Bits:
        """
        Insert values specified in `nums` into current `Bits` object according to `mask`
        Functionally is the inverse of `.extract()` method
            on specified positions denoted by `mask`
        Mask consists of 3 types of markers:
            • *index marker* – digits from 0 to `len(nums)`
            • *delimiter* – any character (except for digit or specified separator character)
            • *separator* – character specified by `sep` (could not be another marker character)
        Each group of adjacent index markers holds position of a separate number to be inserted
            into current `Bits` object (represented as a bit sequence)
        The value of marker digits themselves defines 0-based index of number
            from `nums` argument to be inserted into designated position
        Multiple groups of index markers with the same digit would cause corresponding
            number to be inserted into multiple positions, possibly stripping it
            to the length of its respective group if required
        Delimiter characters denote positions of the bits to be skipped (dash is recommended)
        Separator characters are intended to enhance readability and are simply ignored
        Mask is right-aligned with processed number (to match least-significant bit)
        >>> Bits().pack('0000--1-', 0b100, 1) == Bits(0b0100_0010)
        >>> Bits(0b10).pack('0011 22--', 0b11, 0, 1) == Bits(0b1100_0110)
        >>> Bits(0b1001_1010).pack('00- 111-', 0b11, 1) == Bits(0b1111_0010)
        """

        if sep:
            mask = ''.join(mask.split(sep))
        result = 0  # holds all nums packed together sitting on their corresponding positions
        result_mask = 0  # holds 1s on those bit positions where something was packed
        pos = len(mask)
        for marker, group in groupby(mask):
            num_size = len(tuple(group))
            pos -= num_size
            if marker.isdecimal():
                i = int(marker)
                try:
                    num_mask = 2 ** num_size - 1
                    result |= (nums[i] & num_mask) << pos
                    result_mask |= num_mask << pos
                except IndexError:
                    raise ValueError(f"Invalid mask index marker: {marker}. "
                                     f"Indexes should start from 0 "
                                     f"and not exceed the count of inserted values") from None
        return Bits(self & ~result_mask | result)
