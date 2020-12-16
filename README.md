# PyUtils

**Python utilities for cross-project use**



### Installation

1. clone the repo / download the source distribution
2. `$ pip install <path to project directory>`



### Run tests:

1. Install [`pytest`][pytest] package and [`pytest-lazy-fixture`][lazy_fixture] plugin either by running `$ pip install <path>[test]` or manually
2. `cd` into `/tests` directory
3. Test package:
    - from source: `$ python -m pytest <options>`
    - installed: `$ pytest <options>`

[pytest]: https://pypi.org/project/pytest/ "'pytest' package on PyPi"
[lazy_fixture]: https://pypi.org/project/pytest-lazy-fixture/ "'pytest-lazy-fixture' plugin on PyPi"



## Package contents

- [**`utils`**](#utils) – small utilities and helper objects that do not need a dedicated module
  - [**`test`**](#utilstest) – namespace class with different sample `dict`, `list` and `set` collections
  - [**`bytewise()`**](#utilsbytewise) – return string representation of `byteseq` as hexadecimal uppercase octets separated by `sep`
  - [**`bitwise()`**](#utilsbitwise) – return string representation of `byteseq` as binary octets separated by `sep`
  - [**`@deprecated`**](#utilsdeprecated) – issue `DeprecationWarning` before invoking the wrapee function
  - [**`autorepr()`**](#utilsautorepr) – generate canonical `__repr__()` method using provided `msg`
  - [**`schain()`**](#utilsschain) – SmartChain – extended `itertools.chain()`
  - [**`isdunder()`**](#utilsisdunder) – return whether `name` is a '\_\_double\_underscore\_\_' name (from enum module)
  - [**`issunder()`**](#utilsissunder) – return whether `name` is a '\_single\_underscore\_' name
  - [**`isiterable()`**](#utilsisiterable) – return whether `obj` is iterable, considering `str` and `bytes` are not
  - [**`Disposable`**](#utilsDisposable) – descriptor that clears its value after each access
  - [**`spy`**](#utilsspy) – iterator around given iterable with separate independent iterator branch for lookahead
  - [**`@getter`**](#utilsgetter) – decorator implementing getter-only attribute descriptor
  - [**`@setter`**](#utilssetter) – decorator implementing setter-only attribute descriptor
  - [**`@legacy`**](#utilslegacy) – decorator to mark wrapped function or method is out of use
  - [**`stack()`**](#utilsstack) – print given iterable in a column
  - [**`Dummy`**](#utilsDummy) – mock no-op class returning itself on every attr access or method call
  - [**`null`**](#utilsnull) – sentinel object for denoting the absence of a value
  - [**`clipboard()`**](#utilsclipboard) – put given string into Windows clipboard
  - [**`ignore`**](#utilsignore) – context manager for filtering specified errors
  - [**`@classproperty`**](#utilsclassproperty) – decorator implementing a class-level read-only property
  - [**`Tree`**](#utilsTree) – tree structure converter and tree-style renderer
    - [**`.render()`**](#render) – create tree-like visual representation string
    - [**`.convert()`**](#convert) – build the tree starting from given `root` item top-down following references to child nodes
    - [**`.build()`**](#build) – build the tree out of `items` collection bottom-up following references to parent nodes
  - [**`AttrEnum`**](#utilsAttrEnum) – enum with custom attributes + an automatic `.index` attribute
- [**`bits`**](#bits) – utilities intended for manipulating binary data on a sub-byte level
  - [**`Bits`**](#bitsBits) – wrapper around `int` that treats a number as a bit sequence
    - [**`.set()`**](#set) – set bits on specified `positions` (set to `1`)
    - [**`.clear()`**](#clear) – clear bits on specified `positions` (set to `0`)
    - [**`.mask()`**](#mask) – set/clear bits according to positions of `1`s and `0`s in `mask` string
    - [**`.flag()`**](#flag) – extract one-bit boolean from specified position `pos`
    - [**`.flags()`**](#flags) – convert `n` rightmost bits to tuple of booleans
    - [**`.compose()`**](#compose) – construct a `Bits` object out of given sequence of bits specified in `flags`
    - [**`.extract()`**](#extract) – pull out one or multiple values on sub-byte basis according to `mask`
    - [**`.pack()`**](#pack) – insert values specified in `nums` into current `Bits` object according to `mask`
- [**`typechecking`**](#typechecking) – module for annotation-driven function call typechecking with no inspection of content for container objects
  - [**`@check_args`**](#typecheckingcheck_args) – decorator for typechecking wrapped function / method arguments specified in `arguments`



<br>



## Documentation



## [utils](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py "source code")

**Small utilities and helper objects that do not need a dedicated module**

Intended for use in both application development and interactive Python interpreter sessions



### [utils.test](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L52 "source code")

**Namespace class with different sample `dict`, `list` and `set` collections**



### [utils.bytewise](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L114 "source code")
#### *`bytewise(byteseq: bytes, sep: str = ' ', limit: Union[int, NoneType] = None, show_len: bool = True) -> str`*

**Return string representation of `byteseq` as hexadecimal uppercase octets separated by `sep`**

Functionally is the inverse of [`bytes.fromhex()`][bytes.fromhex]

In case the length of `byteseq` exceeds the value of specified `limit` argument, extra part of
    output is collapsed to an ellipsis and only the last element is shown after it (see example)

If output is trimmed, `show_len` argument tells whether *'(\<n> bytes)'* is appended to output

Raises `ValueError` if `limit` is less than 2

```python
>>> assert bytewise(b'12345', sep='-') == '31-32-33-34-35'
>>> assert bytewise(bytes.fromhex('00 01 42 5A FF')) == '00 01 42 5A FF'
>>> assert bytewise(b'python', limit=5) == '70 79 74 .. 6E (6 bytes)'
```

[bytes.fromhex]: https://docs.python.org/3/library/stdtypes.html#bytes.fromhex "documentation on 'bytes.fromhex()' method"



### [utils.bitwise](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L154 "source code")
#### *`bitwise(byteseq: bytes, sep: str = ' ') -> str`*

**Return string representation of `byteseq` as binary octets separated by `sep`**

```python
>>> assert bitwise(b'abc') == '01100001 01100010 01100011'
>>> assert bitwise(bytes.fromhex('00 0A FF')) == '00000000 00001010 11111111'
```



### [utils.deprecated](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L163 "source code")
#### *`@deprecated(reason: str)`*

**Issue [`DeprecationWarning`][deprecation_warning] before invoking the wrapee function**

Note: [Warning filters][warning_filters] should be enabled in order for the warning to be displayed.
  Minimal required filter is 'default::DeprecationWarning:utils'

If `reason` argument is specified, it will be displayed after the warning message

```python
>>> @deprecated('duck tape')
... def func(): ...
...
>>> func()
DeprecationWarning: Function 'func' is marked as deprecated (duck tape)
```

[deprecation_warning]: https://docs.python.org/3/library/exceptions.html#DeprecationWarning "documentation on 'DeprecationWarning' class"
[warning_filters]: https://docs.python.org/3/library/warnings.html#the-warnings-filter "documentation on Python warning filters"



### [utils.autorepr](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L199 "source code")
#### *`autorepr(msg: str) -> Callable[[Any], str]`*

**Generate canonical `__repr__()` method using provided `msg`**

```python
>>> class Belarus:
...     __repr__ = autorepr('deserves respect')
...
>>> repr(Belarus)
"<utils.autorepr.<locals>.Belarus deserves respect at 0x...>"
```



### [utils.schain](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L215 "source code")
#### *`schain(*items: Union[T, Iterable[T]]) -> Iterator[T]`*

**SmartChain – extended [`itertools.chain()`][itertools.chain]**
  - accepts singular objects as well as iterables
  - treats `str` as items, not iterables

```python
>>> assert [*schain(-1, range(3), 8)] == [-1, 0, 1, 2, 8]  # accepts non-iterable objects
>>> assert [*schain(('foo', 'bar'), 'solid')] == ['foo', 'bar', 'solid'] # does not tear strings apart
>>> assert [*schain(range(3), 3, [], 42)] == [0, 1, 2, 3, 42]  # iterables and items could go in any order
```

[itertools.chain]: https://docs.python.org/3/library/itertools.html#itertools.chain "documentation on 'itertools.chain()' function"



### [utils.isdunder](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L233 "source code")
#### *`isdunder(name: str) -> bool`*

**Return whether `name` is a '\_\_double\_underscore\_\_' name (from [`enum`][enum] module)**

[enum]: https://docs.python.org/3/library/enum.html "documentation on 'enum' module"



### [utils.issunder](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L240 "source code")
#### *`issunder(name: str) -> bool`*

**Return whether `name` is a '\_single\_underscore\_' name**



### [utils.isiterable](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L247 "source code")
#### *`isiterable(obj) -> bool`*

**Return whether `obj` is iterable, considering `str` and `bytes` are not**



### [utils.Disposable](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L255 "source code")

**Descriptor that clears its value after each access**

```python
>>> class Class:
...     attr = Disposable(100500)
...
>>> obj = Class()
>>> assert obj.attr == 100500  # returns initial value
>>> obj.attr = 42  # descriptor value is set to 42
>>> assert obj.attr == 42  # first access returns value
>>> assert obj.attr is None  # subsequent access returns None
```



### [utils.spy](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L282 "source code")

**Iterator around given iterable with separate independent iterator branch for lookahead**

`.lookahead()` returns an iterator that advances the underlying iterable,
  but does not influence main iteration branch

`spy` object itself works just as conventional iterable regardless of `.lookahead()` state

```python
>>> iterator = spy(range(1, 3))  # spy object wraps range(5)
>>> lookahead = iterator.lookahead()  # independent lookahead iterator is created
>>> assert lookahead.__next__() == 1
>>> assert iterator.__next__() == 1
>>> assert list(lookahead) == [2, 3]
>>> assert list(iterator) == [2, 3]
>>> assert list(lookahead) == []  # exhausted
```



### [utils.getter](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L316 "source code")
#### *`@GetterDescriptor`*

**Decorator implementing getter-only attribute descriptor**

Wraps given getter function into descriptor object that uses its return value when
  instance attribute with the same name as was assigned to descriptor itself is acessed

Attribute setting and deletion procedures are left unaffected

Signature of decorated getter method should be `getter(self, value) -> returned`:
  - `value` – the actual value of requested instance attribute stored in instance `__dict__`
  - `returned` – getter return value that is to be returned to outer code requesting the attribute

```python
>>> class GetterExample:
...     @getter
...     def attr(self, value):
...         # handle acquired value somehow...
...         return str(value)
...
>>> instance = GetterExample()
>>> instance.attr = 42
>>> assert instance.__dict__['attr'] == 42  # store unchanged
>>> assert instance.attr == '42'  # acquire modified
```



### [utils.setter](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L362 "source code")
#### *`@SetterDescriptor`*

**Decorator implementing setter-only attribute descriptor**

Wraps given setter function into descriptor object that assigns its return value
  to instance attribute with the same name as was assigned to descriptor itself

Attribute access and deletion procedures are left unaffected

Signature of decorated setter method should be `setter(self, value) -> stored`:
  - `value` – the value being set to instance attribute from outer code
  - `stored` – return value that is to be actually assigned to instance attribute

```python
>>> class SetterExample:
...     @setter
...     def attr(self, value):
...         # handle reassignment somehow...
...         return str(value)
...
>>> instance = SetterExample()
>>> instance.attr = 42
>>> assert instance.__dict__['attr'] == '42'  # store modified
>>> assert instance.attr == '42'  # acquire unchanged
```



### [utils.legacy](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L401 "source code")
#### *`@legacy`*

**Decorator to mark wrapped function or method is out of use**

Returns new function that raises `RuntimeError` when called



### [utils.stack](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L412 "source code")
#### *`stack(iterable, *, indent=4)`*

**Print given iterable in a column**



### [utils.Dummy](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L422 "source code")

**Mock no-op class returning itself on every attr access or method call**

Intended for avoiding both if-checks and attribute errors when dealing with optional values

Evaluates to `False` on logical operations

```python
>>> dummy = Dummy('whatever', accepts='any args')
>>> assert str(dummy) == 'Dummy'
>>> assert dummy.whatever is dummy
>>> assert dummy.method('any', 'args') is dummy
>>> assert dummy('any', 'args') is dummy
>>> assert bool(dummy) is False
```



### [utils.null](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L453 "source code")

**Sentinel object for denoting the absence of a value**

Evaluates to `False` on logical comparisons

Should not be used as a distinct value for some attribute or variable



### [utils.clipboard](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L478 "source code")
#### *`clipboard(text: str)`*

**Put given string into Windows clipboard**

Raises [`subprocess.CalledProcessError`][called_process_error] if underlying [`clip`][clip] utility returns non-zero exit code

[called_process_error]: https://docs.python.org/3/library/subprocess.html#subprocess.CalledProcessError "documentation on 'subprocess.CalledProcessError' class"
[clip]: https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/clip "documentation on 'clip' Windows shell command"



### [utils.ignore](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L486 "source code")

**Context manager for filtering specified errors**

Accepts any amount of exception types, subclasses are respected

If no error type is provided, it returns [`nullcontext`][nullcontext] which does nothing – 
  that simplifies usage in case exception types are calculated dymamically

```python
>>> with ignore(LookupError):
...     raise KeyError()  # KeyError is a subclass of LookupError, so it is filtered out
...
```
```python
>>> with ignore(LookupError):
...     raise RuntimeError('message')  # RuntimeError does not pass a filter, so it is raised
...
RuntimeError: message
```
```python
>>> with ignore():
...     raise Exception('message')  # no exception types are being passed, so nothing is filtered
...
Exception: message
```

[nullcontext]: https://docs.python.org/3/library/contextlib.html#contextlib.nullcontext "documentation on 'contextlib.nullcontext' context manager"



### [utils.classproperty](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L522 "source code")
#### *`@classproperty`*

**Decorator implementing a class-level read-only property**



### [utils.Tree](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L533 "source code")

**Tree structure converter and tree-style renderer**

Intended to be used mainly for display purposes

Does not handle cycle references for now

```python
>>> exceptions = [...]  # list of all python exceptions
>>> tree = Tree.build(items=exceptions, naming='__name__', parents='__base__')
>>> assert str(tree) == tree.render()
>>> tree.render()
object
└── BaseException
    ├── Exception
    │   ├── ArithmeticError
    │   │   ├── FloatingPointError
    │   │   ├── OverflowError
    │   │   └── ZeroDivisionError
    │   ├── AssertionError
    │   ├── AttributeError
    ...
```


> ### [.render](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L577 "source code")
> #### *`.render(self, style: Literal['strict', 'smooth', 'empty'] = 'strict', empty: str = '<Empty tree>')`*
> 
> **Create tree-like visual representation string**
> 
> Strings used for visualising tree branches are determined by `style` argument
> 
> Empty tree representation is specified by `empty` argument
> 
> 
> ### [.convert](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L603 "source code")
> #### *`.convert(root: 'Item', naming: 'Union[str, NameHandle]', children: 'Union[str, ChildrenHandle]') -> 'Tree'`*
> 
> **Build the tree starting from given `root` item top-down following references to child nodes**
> 
> The name for each generated node is determined by `naming` argument, which can be:
>   - string – defines the name of an item's attribute, so that `node.name = item.<name>`
>   - callable – defines a callable of a single argument, so that `node.name = <callable>(item)`
> 
> Similarly, `children` argument defines a handle for acquiring a list of item's children.
>   It could be whether a item's attribute name or a single-argument callable hook
> 
> 
> ### [.build](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L629 "source code")
> #### *`.build(items: 'Iterable[Item]', naming: 'Union[str, NameHandle]', parent: 'Union[str, ParentHandle]' = None) -> 'Tree'`*
> 
> **Build the tree out of `items` collection bottom-up following references to parent nodes**
> 
> Semantics of `naming` and `parent` arguments is similar to corresponding arguments of `.convert()` method
> 
> Elements of `items` collection should be hashable



### [utils.AttrEnum](https://github.com/GlebMorgan/PyUtils/blob/master/utils/utils.py#L671 "source code")

**Enum with custom attributes + an automatic `.index` attribute**

`AttrEnum` attributes are declared by assigning desired names to special `__fields__` variable
  on the very first line of enum class body (somewhat similar to Python [`__slots__`][slots])

Attribute values are set by assigning each `AttrEnum` member with a tuple of values,
  that correspond to specified `__fields__`; missing values fallback to `None`

`.index` attribute is set automatically and defaults to enum member index number within order of declaration

Both `.value` and `.index` attributes may be overridden by providing their names in `__fields__`

If `__fields__` tuple is not specified, only `.index` attribute is added to enum member implicitly;
  besides that the class would generally behave like conventional [`Enum`][enum]

```python
>>> class Sample(AttrEnum):
...     __fields__ = 'attr1', 'attr2', 'attr3'
...     A = 'data_A', 10, True
...     B = 'data_B', 42
...     C = 'data_C', 77
...
>>> member = Sample.B
>>> assert member.name == 'B'
>>> assert member.index == 1  # counts from 0 in order of declaration
>>> assert member.value == ('data_B', 42, None)  # values are filled up to match __fields__
>>> assert member.attr1 == 'data_B'
>>> assert member.attr2 == 42
>>> assert member.attr3 is None  # if attr is not specified, it defaults to None
>>> assert repr(member) == "<Sample.B: attr1='data_B', attr2=42, attr3=None>"
```
```python
>>> class ValueSample(AttrEnum):
...     __fields__ = 'index', 'value'
...     A = 1, 'data_A'
...     B = 3, 'data_B'
...     C = 2, 'data_C'
...
>>> member = ValueSample.B
>>> assert member.name == 'B'
>>> assert member.index == 3  # index is overridden
>>> assert member.value == 'data_B'  # value is overridden as well
>>> assert repr(member) == "<ValueSample.B: index=3, value='data_B'>"  # repr keeps unified format
```
```python
>>> class VoidSample(AttrEnum):
...     A = 2
...     B = 7
...     C = 9
...
>>> member = VoidSample.B
>>> assert member.name == 'B'
>>> assert member.index == 1  # .index defaults to enum member index number
>>> assert member.value == 7  # .value defaults to whatever member is assigned to
>>> assert repr(member) == "<VoidSample.B: 7>"
```

[slots]: https://docs.python.org/3/reference/datamodel.html#object.__slots__ "documentation on python '__slots__' feature"



<br>



## [bits](https://github.com/GlebMorgan/PyUtils/blob/master/utils/bits.py "source code")

**Utilities intended for manipulating binary data on a sub-byte level**



### [bits.Bits](https://github.com/GlebMorgan/PyUtils/blob/master/utils/bits.py#L16 "source code")

**Wrapper around `int` treating a number as a bit sequence**

Provides a set of tools to manipulate, extract, insert, split, combine
  individual bits and bit sequences within a processed number

All methods intended to modify the value in-place return a newly created `Bits` object
  since there's no way of manipulating underlying `int` value directly


> ### [.set](https://github.com/GlebMorgan/PyUtils/blob/master/utils/bits.py#L25 "source code")
> #### *`.set(self, *positions: int) -> Bits`*
> 
> **Set bits on specified `positions` (set to `1`)**
> 
> Position indexes start from zero and are counted from rightmost bit to the left
> 
> ```python
> >>> Bits(0b01).set(1) == Bits(0b11)
> >>> Bits(0b1010).set(0, 2) == Bits(0b1111)
> >>> Bits(0b0).set(3) == Bits(0b1000)
> ```
> 
> 
> ### [.clear](https://github.com/GlebMorgan/PyUtils/blob/master/utils/bits.py#L42 "source code")
> #### *`.clear(self, *positions: int) -> Bits`*
> 
> **Clear bits on specified `positions` (set to `0`)**
> 
> Position indexes start from zero and are counted from rightmost bit to the left
> 
> ```python
> >>> Bits(0b01).clear(0) == Bits(0b0)
> >>> Bits(0b1010).clear(3) == Bits(0b0010)
> >>> Bits(0b11).clear(0, 2) == Bits(0b10)
> ```
> 
> 
> ### [.mask](https://github.com/GlebMorgan/PyUtils/blob/master/utils/bits.py#L59 "source code")
> #### *`.mask(self, mask: str) -> Bits`*
> 
> **Set/clear bits according to positions of `1`s and `0`s in `mask` string**
> 
> Mask consists of 3 types of markers:
>   - `1` – sets the the bit on corresponding position
>   - `0` – clears the corresponding bit
>   - `-` (dash) – leaves the corresponding bit unchanged
> 
> Mask may use an arbitrary character distinct from `0` and `1`
>   to denote position of a bit to be skipped
> 
> Mask is right-aligned with processed number (to match least-significant bit)
> 
> ```python
> >>> Bits(0b0101).mask('-01-') == Bits(0b0011)
> >>> Bits(0b1100).mask('11') == Bits(0b1111)
> >>> Bits(0b1111).mask('-') == Bits(0b1111)
> ```
> 
> 
> ### [.flag](https://github.com/GlebMorgan/PyUtils/blob/master/utils/bits.py#L82 "source code")
> #### *`.flag(self, pos: int) -> bool`*
> 
> **Extract one-bit boolean from specified position `pos`**
> 
> Position index starts from zero and is counted from rightmost bit to the left
> 
> ```python
> >>> Bits(0b0100).flag(2) == True
> ```
> 
> 
> ### [.flags](https://github.com/GlebMorgan/PyUtils/blob/master/utils/bits.py#L90 "source code")
> #### *`.flags(self, n: int) -> Tuple[bool, ...]`*
> 
> **Convert `n` rightmost bits to tuple of booleans**
> 
> Functionally is the inverse of `.compose()` method
> 
> Resulting flags order conforms to default bit indexing - right to left
> 
> ```python
> >>> Bits(0b0100).flags(3) == (False, False, True)
> ```
> 
> 
> ### [.compose](https://github.com/GlebMorgan/PyUtils/blob/master/utils/bits.py#L100 "source code")
> #### *`.compose(*flags: bool) -> Bits`*
> 
> **Construct a `Bits` object out of given sequence of bits specified in `flags`**
> 
> Functionally is the inverse of `.flags()` method
> 
> The bits placing order conforms to default bit indexing – right to left
> 
> ```python
> >>> Bits.compose(False, False, True, False) == Bits(0x100)
> ```
> 
> 
> ### [.extract](https://github.com/GlebMorgan/PyUtils/blob/master/utils/bits.py#L109 "source code")
> #### *`.extract(self, mask: str, *, sep: str = ' ') -> Tuple[int, ...]`*
> 
> **Pull out one or multiple values on sub-byte basis according to `mask`**
> 
> Mask consists of 3 types of markers:
>   - *number marker* – digits 0..9
>   - *delimiter* – any character (except for digit or specified separator character)
>   - *separator* – character specified by `sep` (could not be another marker character)
> 
> Each group of adjacent number markers holds position of a separate number to be extracted
>   from current `Bits` object (represented as a bit sequence)
> 
> The order of extraction is defined by value of marker digits themselves
> 
> Multiple groups with the same digit would raise a `ValueError`
> 
> Delimiter characters denote positions of the bits to be skipped (dash is recommended)
> 
> Separator characters are intended to enhance readability and are simply ignored
> 
> Mask is right-aligned with processed number (to match least-significant bit)
> 
> ```python
> >>> Bits(0b0001_1100).extract('111--') == (0b111,)
> >>> Bits(0b1100_0110).extract('2221 11-3') == (0b1, 0b110, 0b0)
> >>> Bits(0b0011_1010).extract('1122 2-13') -> ValueError  # duplicating marker group: 1
> ```
> 
> 
> ### [.pack](https://github.com/GlebMorgan/PyUtils/blob/master/utils/bits.py#L168 "source code")
> #### *`.pack(self, mask: str, *nums: int, sep: str = ' ') -> Bits`*
> 
> **Insert values specified in `nums` into current `Bits` object according to `mask`**
> 
> Functionally is the inverse of `.extract()` method
>   on specified positions denoted by `mask`
> 
> Mask consists of 3 types of markers:
>   - *index marker* – digits from 0 to `len(nums)`
>   - *delimiter* – any character (except for digit or specified separator character)
>   - *separator* – character specified by `sep` (could not be another marker character)
> 
> Each group of adjacent index markers holds position of a separate number to be inserted
>   into current `Bits` object (represented as a bit sequence)
> 
> The value of marker digits themselves defines 0-based index of number
>   from `nums` argument to be inserted into designated position
> 
> Multiple groups of index markers with the same digit would cause corresponding
>   number to be inserted into multiple positions, possibly stripping it
>   to the length of its respective group if required
> 
> Delimiter characters denote positions of the bits to be skipped (dash is recommended)
> 
> Separator characters are intended to enhance readability and are simply ignored
> 
> Mask is right-aligned with processed number (to match least-significant bit)
> 
> ```python
> >>> Bits().pack('0000--1-', 0b100, 1) == Bits(0b0100_0010)
> >>> Bits(0b10).pack('0011 22--', 0b11, 0, 1) == Bits(0b1100_0110)
> >>> Bits(0b1001_1010).pack('00- 111-', 0b11, 1) == Bits(0b1111_0010)
> ```



<br>



## [typechecking](https://github.com/GlebMorgan/PyUtils/blob/master/utils/typechecking.py "source code")

**Module for annotation-driven function call typechecking with no inspection of content for container objects**

Ideologically intended for human-bound use cases such as rough user input viability checks

<details>
<summary>Click to expand</summary>
<br>

API:
  - `@check_args` – decorator that performs typechecking on specified (or all) arguments
    of the decorated function / method immediately before the actual call

Typecheck machinery glossary:
  - type annotation (annotation) - entire annotation expression:
    `Dict[str, Union[List[int], int]]`, etc.
  - type specificator (typespec) - any structural component of type annotation:
    `Iterable[int]`, `Tuple`, `Union[int, Collection[int]]`, `Any`, `type`, etc.
  - type origin (basetype) – upper component of some given subscriptable typespec:
    `Union`, `List`, `int`, `TypeVar`, etc.
  - type arguments (typeargs) - set of arguments of some given subscriptable typespec:
    `[str, Dict[str, int]]`, `[]`, `[Optional[Callable]]`, `[bool, ...]`, etc.

Supported features:
  - first-level typechecking against provided type annotation
  - all type specificators provided by [`typing`][typing] 
    module for Python 3.8
  - structure checks for `Tuple`s, excluding homogeneous tuples (like `Tuple[str, ...]`)
  - structure checks for `TypedDict`s
  - subclass checks for `NamedTuple`s
  - typechecking against bound types and constraints of `TypeVar`s
  - runtime-checkable `Protocol`s
  - simplified `IO` class checks
  - automatic `None` –> `NoneType` conversion (by [`typing.get_type_hints()`][get_type_hints] used under the hood)

Behaviours that this module was **NOT** designed to support:
  - inspecting of contents for iterables and containers, including homogeneous tuple typespecs
  - inspecting callable signatures
  - inspecting annotations of interface and protocol classes
  - checks that involve applying a specific type to generic classes
  - rigorous subclass checks of complex type specificators inside `Type[...]`
  - complicated `IO` type checks
  - resolving `ForwardRef`s

Supported type specifications:
  - Bare types, including `NoneType`
  - `SpecialForm`s:
      `Any`, `ClassVar`, `Final`, `Literal`, `Optional`, `Union`
  - Interfaces:
      `Awaitable`, `Callable`, `ContextManager`, `AsyncContextManager`, `Coroutine`, 
      `Generator`, `AsyncGenerator`, `Hashable`, `Iterable`, `AsyncIterable`, `Iterator`, 
      `AsyncIterator`, `Reversible`, `Sized`
  - Protocols:
      `SupportsAbs`, `SupportsBytes`, `SupportsComplex`, `SupportsFloat`, 
      `SupportsIndex`, `SupportsInt`, `SupportsRound`
  - Custom runtime-checkable protocols (derived from `Protocol`)
  - Containers:
      `ChainMap`, `Collection`, `Container`, `Counter`, `Deque`, `Dict`, `DefaultDict`, `OrderedDict`, 
      `ItemsView`, `KeysView`, `ValuesView`, `List`, `Mapping`, `MutableMapping`, `MappingView`, 
      `Sequence`, `MutableSequence`, `Set`, `FrozenSet`, `AbstractSet`, `MutableSet`, `Tuple`
  - Type references:
      `Type`, `ByteString`, `Pattern`, `Match`, `IO`, `TextIO`, `BinaryIO`
  - `Generic` classes
  - `TypedDict`s
  - `NamedTuple`s and `NamedTuple` class itself
  - `TypeVar`s

[typing]: https://docs.python.org/3/library/typing.html "documentation on 'typing' module"
[get_type_hints]: https://docs.python.org/3/library/typing.html#typing.get_type_hints "documentation on 'typing.get_type_hints' function"

</details>



### [typechecking.check_args](https://github.com/GlebMorgan/PyUtils/blob/master/utils/typechecking.py#L329 "source code")
#### *`@check_args(*arguments: str, check_defaults: bool = False)`*

**Decorator for typechecking wrapped function / method arguments specified in `arguments`**

Raises `TypecheckError` if typecheck fails, otherwise returns `None`

Checks are performed against argument annotations of wrapped callable at the time it is being called

If `arguments` are omitted, typeckecking is performed on all the parameters being passed

Default values of function / method arguments are not typechecked unless `check_defaults=True` is provided

If wrapped function / method is already decorated, `@check_args` should be applied beforehand in most cases

Though `classmethod`s and `staticmehtod`s are treated properly and may be simply decorated over

If some argument of wrapped callable has default value set to `None`, its annotation is
  automatically converted to `Optional[<annotation>]` (by [`typing.get_type_hints()`][get_type_hints] used under the hood)

```python
>>> @check_args
... def func(a: Union[int, Dict[str, int], Tuple[Any, str]]):
...     ...
...
>>> func(1)  # typechecks: `1` is an `int`
>>> func(True)  # typechecks: `bool` is a subclass of `int`
>>> func({})  # typechecks: empty dict is a `dict`
>>> func({1: True, 2: 's'})  # typechecks: dict contents are not inspected
>>> func((object, 's'))  #typechecks: argument is a `tuple` and its structure matches annotation signature
>>> func(None)  # fails: `NoneType` does not match any one of given specifications
>>> func(['s', 1])  # fails: `list` is not an `int`, nor a `dict`, nor a `tuple`
>>> func(('s', 0))  # fails: the second item of the tuple does not match given `str` specification
>>> func((0, 's', 'extra'))  # fails: tuple has an extra element
```
```python
>>> @check_args('a', 'b')
... def func(a: Any, b: int, c: bool):
...     ...
...
>>> func(object, 1, 's')  # typechecks: only 'a' and 'b' arguments are checked
```
