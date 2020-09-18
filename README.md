# PyUtils
Python utilities for cross-project use
TODO: how to run tests, benchmarks and other utilities

## Package contents

- **`sampledict`** – dictionary for testing purposes
- **`Bits`** – wrapper around `int` treating a number as a bit sequence
  - **`.set()`** – set bits on specified `positions` (set to `1`)
  - **`.clear()`** – clear bits on specified `positions` (set to `0`)
  - **`.mask()`** – set/clear bits according to positions of `1`s and `0`s in `mask` string
  - **`.flag()`** – extract one-bit boolean from specified position `pos`
  - **`.flags()`** – convert `n` rightmost bits to tuple of booleans
  - **`.compose()`** – construct a `Bits` object out of given sequence of bits specified in `flags`
  - **`.extract()`** – pull out one or multiple values on sub-byte basis according to `mask`
  - **`.extract2()`** – a 25% slower implementation of `.extract()` with same functionality
  - **`.pack()`** – insert values specified in `nums` into current `Bits` object according to `mask`
- **`bytewise`** – return string representation of `byteseq` as hexadecimal uppercase octets separated by `sep`


## Documentation

#### `sampledict`

##### Dictionary for testing purposes
Contains objects of all common Python types + self-reference

---

### `Bits`

##### Wrapper around `int` treating a number as a bit sequence

Provides a set of tools to manipulate, extract, insert, split, combine
  individual bits and bit sequences within a processed number

All methods intended to modify the value in-place return a newly created `Bits` object
  since there's no way of manipulating underlying `int` value directly

---

#### `Bits.set(self, *positions: int) -> Bits`

##### Set bits on specified `positions` (set to `1`)

Position indexes start from zero and are counted from rightmost bit to the left

```python
>>> Bits(0b01).set(1) == Bits(0b11)
>>> Bits(0b1010).set(0, 2) == Bits(0b1111)
>>> Bits(0b0).set(3) == Bits(0b1000)
```

---

#### `Bits.clear(self, *positions: int) -> Bits`

##### Clear bits on specified `positions` (set to `0`)

Position indexes start from zero and are counted from rightmost bit to the left

```python
>>> Bits(0b01).clear(0) == Bits(0b0)
>>> Bits(0b1010).clear(3) == Bits(0b0010)
>>> Bits(0b11).clear(0, 2) == Bits(0b10)
```

---

#### `Bits.mask(self, mask: str) -> Bits`

##### Set/clear bits according to positions of `1`s and `0`s in `mask` string

Mask consists of 3 types of markers:
  - `1` – sets the the bit on corresponding position
  - `0` – clears the corresponding bit
  - `-` (dash) – leaves the corresponding bit unchanged

Mask may use an arbitrary character distinct from `0` and `1`
  to denote position of a bit to be skipped

Mask is right-aligned with processed number (to match least-significant bit)

```python
>>> Bits(0b0101).mask('-01-') == Bits(0b0011)
>>> Bits(0b1100).mask('11') == Bits(0b1111)
>>> Bits(0b1111).mask('-') == Bits(0b1111)
```

---

#### `Bits.flag(self, pos: int) -> bool`

##### Extract one-bit boolean from specified position `pos`

Position index starts from zero and is counted from rightmost bit to the left

```python
>>> Bits(0b0100).flag(2) == True
```

---

#### `Bits.flags(self, n: int) -> Tuple[bool, ...]`

##### Convert `n` rightmost bits to tuple of booleans

Functionally is the inverse of `.compose()` method

Resulting flags order conforms to default bit indexing - right to left

```python
>>> Bits(0b0100).flags(3) == (False, False, True)
```

---

#### `Bits.compose(*flags: bool) -> Bits`

##### Construct a `Bits` object out of given sequence of bits specified in `flags`

Functionally is the inverse of `.flags()` method

The bits placing order conforms to default bit indexing – right to left

```python
>>> Bits.compose(False, False, True, False) == Bits(0x100)
```

---

#### `Bits.extract(self, mask: str, *, sep: str = ' ') -> Tuple[int, ...]`

##### Pull out one or multiple values on sub-byte basis according to `mask`

Mask consists of 3 types of markers:
  - *number marker* – digits 0..9
  - *delimiter* – any character (except for digit or specified separator character)
  - *separator* – character specified by `sep` (could not be another marker character)

Each group of adjacent number markers holds position of a separate number to be extracted
  from current `Bits` object (represented as a bit sequence)

The order of extraction is defined by value of marker digits themselves

Multiple groups with the same digit would raise a `ValueError`

Delimiter characters denote positions of the bits to be skipped (dash is recommended)

Separator characters are intended to enhance readability and are simply ignored

Mask is right-aligned with processed number (to match least-significant bit)

```python
>>> Bits(0b0001_1100).extract('111--') == (0b111,)
>>> Bits(0b1100_0110).extract('2221 11-3') == (0b1, 0b110, 0b0)
>>> Bits(0b0011_1010).extract('1122 2-13') -> ValueError  # duplicating marker group: 1
```

---

#### `Bits.extract2(self, mask: str, *, sep: str = ' ') -> List[int]`

##### A 25% slower implementation of `.extract()` with same functionality

This variant also returns a `list` instead of a `tuple`

---

#### `Bits.pack(self, mask: str, *nums: int, sep: str = ' ') -> Bits`

##### Insert values specified in `nums` into current `Bits` object according to `mask`

Functionally is the inverse of `.extract()` method
  on specified positions denoted by `mask`

Mask consists of 3 types of markers:
  - *index marker* – digits from 0 to `len(nums)`
  - *delimiter* – any character (except for digit or specified separator character)
  - *separator* – character specified by `sep` (could not be another marker character)

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

```python
>>> Bits().pack('0000--1-', 0b100, 1) == Bits(0b0100_0010)
>>> Bits(0b10).pack('0011 22--', 0b11, 0, 1) == Bits(0b1100_0110)
>>> Bits(0b1001_1010).pack('00- 111-', 0b11, 1) == Bits(0b1111_0010)
```

---

#### `bytewise(byteseq: bytes, sep: str = ' ', limit: int = None, show_len: bool = True) -> str`

##### Return string representation of `byteseq` as hexadecimal uppercase octets separated by `sep`

Functionally is the inverse of `bytes.fromhex()`

In case the length of `byteseq` exceeds the value of specified `limit` argument, extra part of
  output is collapsed to an ellipsis and only the last element is shown after it (see example)

If output is trimmed, `show_len` argument tells whether '(`<n>` bytes)' is appended to output

```python
>>> bytewise(b'12345', sep='-') == '31-32-33-34-35'
>>> bytewise(bytes.fromhex('00 01 42 5A FF')) == '00 01 42 5A FF'
>>> bytewise(b'python', limit=5) == '70 79 74 .. 6E (6 bytes)'
```