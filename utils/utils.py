from __future__ import annotations

import re
from itertools import islice, repeat
from typing import Any, Callable, Iterable, Iterator

from wrapt import decorator


# TODO: short module description, purpose



__all__ = ['test', 'bytewise', 'bitwise', 'deprecated', 'autorepr', 'typename', 'spy']


class test:
    """Sample collections namespace class"""

    dict = dict(a=0, b=True, c='item', d=42, e=..., f=1.0, g=None, h=(1, 2, 3))
    list = [*dict.values()]
    set = {*list}
    # Number collections
    ndict = {i: f'item{i}' for i in range(10)}
    nlist = [*ndict.keys()]
    nset = {*nlist}

    # String collections
    sdict = {
        'beautiful': 'better than ugly',
        'explicit': 'better than implicit',
        'simple': 'better than complex',
        'complex': 'better than complicated',
        'flat': 'better than nested',
        'sparse': 'better than dense',
        'readability': 'counts',
        'practicality': 'beats purity',
        'errors': 'never passed silently',
        'namespaces': 'one honking great idea',
    }
    slist = [*sdict.keys()]
    sset = {*slist}

    # Mixed-type collections
    mdict = {
        1: 'a',
        2: 'b',
        3: 'c',
        'None': None,
        'bool': True,
        'str': 'python',
        'lstr': 'long example string that presumably have little chances '
                'to fit onto one single line (unless you use 4K monitor :)',
        'mstr': '1st str' + '\\n' + '2nd str',
        'ellipsis': ...,
        'list': [1, 2, 3, 4, 5, ('a', 'b', 'c'), ..., None],
        'empty': [],
        'tuple': tuple(range(12)),
        'dict': {1: 'first', 2: 'second'},
        'object': object(),
        'class': RuntimeError,
        'function': print,
        'module': re,
    }
    mlist = [*mdict.values()]
    mset = {item for item in mlist if item.__hash__}

    # Mixed-type collections with self-reference
    selfdict = dict.copy();  selfdict['self'] = selfdict
    selflist = [*dict.values()];  selflist.append(selflist)
    # NOTE: `selfset` does not exist due to self-reference is unhashable

    # Names of all collections defined
    all = [name for name in locals() if name[0] != '_']


def bytewise(byteseq: bytes, sep: str = ' ', limit: int = None, show_len: bool = True) -> str:
    """
    Return string representation of `byteseq` as hexadecimal uppercase octets separated by `sep`
    Functionally is the inverse of `bytes.fromhex()`
    In case the length of `byteseq` exceeds the value of specified `limit` argument, extra part of
        output is collapsed to an ellipsis and only the last element is shown after it (see example)
    If output is trimmed, `show_len` argument tells whether '(`<n>` bytes)' is appended to output
    >>> assert bytewise(b'12345', sep='-') == '31-32-33-34-35'
    >>> assert bytewise(bytes.fromhex('00 01 42 5A FF')) == '00 01 42 5A FF'
    >>> assert bytewise(b'python', limit=5) == '70 79 74 .. 6E (6 bytes)'
    """

    octets = map(''.join, zip(*repeat(iter(byteseq.hex().upper()), 2)))
    if limit is None or len(byteseq) <= limit:
        return sep.join(octets)
    if limit < 2:
        raise ValueError("Cannot limit sequence to less than 2 bytes")
    else:
        head = islice(octets, limit - 2)  # account for last byte + '..'
        last = byteseq[-1:].hex().upper()
        appendix = f' ({len(byteseq)} bytes)' if show_len else ''
        return sep.join((*head, '..', last)) + appendix


def bytewise2(byteseq: bytes, sep: str = ' ', limit: int = None, show_len: bool = True) -> str:
    """
    More readable, but 2.5 times slower implementation of `bytewise()`
    """

    octets = (f'{byte:02X}' for byte in byteseq)
    if limit is None or len(byteseq) <= limit:
        return sep.join(octets)
    else:
        head = islice(octets, limit - 2)
        last = f'{byteseq[-1]:02X}'
        appendix = f' ({len(byteseq)} bytes)' if show_len else ''
        return sep.join((*head, '..', last)) + appendix


def bitwise(byteseq: bytes, sep: str = ' ') -> str:
    """
    Return string representation of `byteseq` as binary octets separated by `sep`
    >>> assert bitwise(b'abc') == '01100001 01100010 01100011'
    >>> assert bitwise(bytes.fromhex('00 0A FF')) == '00000000 00001010 11111111'
    """
    return sep.join(f"{byte:08b}" for byte in byteseq)


def deprecated(reason: str):
    """
    Issue `DeprecationWarning` before invoking the wrapee function
    Note: Warning filters should be enabled in order for the warning to be displayed.
        Minimal required filter is 'default::DeprecationWarning:utils'
    If `reason` argument is specified, it will be displayed after the warning message
    >>> @deprecated('duck tape')
    >>> def func(): ...
    >>> func()
        "DeprecationWarning: Function 'func' is marked as deprecated (duck tape)"
    """

    @decorator
    def deprecation_wrapper(wrapped, instance, args, kwargs):
        from warnings import warn
        wrapee = wrapped.__class__.__name__.replace('type', 'class')
        message = f"{wrapee.capitalize()} '{wrapped.__name__}' is marked as deprecated"
        if details:
            message += f' ({details})'
        warn(message, category=DeprecationWarning, stacklevel=3)
        return wrapped(*args, **kwargs)

    if isinstance(reason, str):
        # Infer decorator is used with an argument,
        #   thus store `reason` in a closure from `deprecation_wrapper`
        details = reason
        return deprecation_wrapper
    else:
        # Infer decorator is used without arguments,
        #   in this case `reason` is expected to be an object to be wrapped
        details = ''
        return deprecation_wrapper(reason)


def autorepr(msg: str) -> Callable:
    """
    Generate canonical `__repr__()` method using provided `msg`
    >>> class Belarus:
    ...     __repr__ = autorepr('deserves respect')
        <utils.autorepr.<locals>.Belarus deserves respect at 0x...>
    """

    def __repr__(self):
        cls = self.__class__
        return f"<{cls.__module__}.{cls.__qualname__} {msg} at {hex(id(self))}>"
    return __repr__


def schain(*items):
    """
    SmartChain – extended `itertools.chain()`
      • accepts singular objects as well as iterables
      • treats `str` as items, not iterables
    >>> assert [*schain(-1, range(3), 8)] == [-1, 0, 1, 2, 8]  # accepts non-iterable objects
    >>> assert [*schain(('foo', 'bar'), 'solid')] == ['foo', 'bar', 'solid'] # does not tear strings apart
    >>> assert [*schain(range(3), 3, [], 42)] == [0, 1, 2, 3, 42]  # iterables and items could go in any order
    """
    for item in items:
        if isinstance(item, str):
            yield item
        elif hasattr(item, '__iter__'):
            yield from item
        else:
            yield item


def isdunder(name: str) -> bool:
    """Return whether `name` is a __double_underscore__ name (from enum module)"""
    return (name[:2] == name[-2:] == '__' and
            name[2:3] != '_' and name[-3:-2] != '_' and
            len(name) > 4)


def issunder(name):
    """Return whether `name` is a _single_underscore_ name"""
    return (name[:1] == name[-1:] == '_' and
            name[1:2] != '_' and name[-2:-1] != '_' and
            len(name) > 2)


def isiterable(obj) -> bool:
    """Return whether `obj` is iterable, considering `str` and `bytes` are not"""
    if isinstance(obj, (str, bytes)):
        return False
    else:
        return isinstance(obj, Iterable)


def typename(obj: Any) -> str:
    """Return simple name of the class of given object"""
    return obj.__class__.__name__


class Disposable:
    """
    Descriptor that clears its value after each access
    >>> class Class:
    ...     attr = Disposable(100500)
    >>> obj = Class()
    >>> assert obj.attr == 100500  # returns initial value
    >>> obj.attr = 42  # descriptor value is set to 42
    >>> assert obj.attr == 42  # first access returns value
    >>> assert obj.attr is None  # subsequent access returns None
    """

    def __init__(self, value=None):
        self.value = value

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = self.value
        self.value = None
        return value

    def __set__(self, instance, value):
        self.value = value


class spy:
    """
    Iterator around given iterable with separate independent iterator branch for lookahead
    `.lookahead()` returns an iterator that advances the underlying iterable,
        but does not influence on main iteration branch
    `spy` object itself works just as conventional iterable regardless of `.lookahead()` state
    >>> iterator = spy(range(1, 3))  # spy object wraps range(5)
    >>> lookahead = iterator.lookahead()  # independent lookahead iterator is created
    >>> assert lookahead.__next__() == 1
    >>> assert iterator.__next__() == 1
    >>> assert list(lookahead) == [2, 3]
    >>> assert list(iterator) == [2, 3]
    >>> assert list(lookahead) == []  # exhausted
    """

    def __init__(self, iterable):
        self.source = iter(iterable)
        self.cache = []

    def __iter__(self):
        return self

    def __next__(self):
        if self.cache:
            return self.cache.pop(0)
        else:
            return next(self.source)

    def lookahead(self) -> Iterator:
        for item in self.source:
            self.cache.append(item)
            yield item


class GetterDescriptor:
    """
    Decorator implementing getter-only attribute descriptor
    Wraps given getter function into descriptor object that uses its return value when
        instance attribute with the same name as was assigned to descriptor itself is acessed
    Attribute setting and deletion procedures are left unaffected
    Signature of decorated getter method should be `getter(self, value) -> returned`:
        • `value` – the actual value of requested instance attribute stored in instance `__dict__`
        • `returned` – getter return value that is to be returned to outer code requesting the attribute
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
    """

    # NOTE: __slots__ break dynamic docstrings

    def __init__(self, func):
        self.name: str
        self.getter = func
        self.__doc__ = func.__doc__

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            value = instance.__dict__[self.name]
        except KeyError:
            message = f"'{instance.__class__.__name__}' object has no attribute '{self.name}'"
            raise AttributeError(message) from None
        return self.getter(instance, value)

    def __set__(self, instance, value):
        # Required to make the class a data descriptor
        instance.__dict__[self.name] = value


class SetterDescriptor:
    """
    Decorator implementing setter-only attribute descriptor
    Wraps given setter function into descriptor object that assigns its return value
        to instance attribute with the same name as was assigned to descriptor itself
    Attribute access and deletion procedures are left unaffected
    Signature of decorated setter method should be `setter(self, value) -> stored`:
        • `value` – the value being set to instance attribute from outer code
        • `stored` – return value that is to be actually assigned to instance attribute
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
    """

    # NOTE: __slots__ break dynamic docstrings

    def __init__(self, func):
        self.name: str
        self.setter = func
        self.__doc__ = func.__doc__

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        instance.__dict__[self.name] = self.setter(instance, value)


getter = GetterDescriptor
setter = SetterDescriptor


def legacy(function):
    """
    Decorator to mark wrapped function or method is out of use
    Raises `RuntimeError` if an attempt to call the wrapped object is made
    """
    def wrapper(*args, **kwargs):
        obj_type: str = function.__class__.__name__.replace('type', 'class')
        raise RuntimeError(f"{obj_type} '{function.__name__}' is marked as legacy")
    return wrapper


# TODO: Null - sentinel object for denoting absence of value
#   Should never be assigned to anything by user code
#   Make NullType a singleton
#   Leave NullType defined inside the module the usual way, but just do not include it into __all__


# CONSIDER: listAttrs() coloring attrs based on type (method, function, dict attr, inherited attr, etc.)
