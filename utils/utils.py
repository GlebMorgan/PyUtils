from __future__ import annotations

import re
from itertools import islice, repeat
from typing import Any, Callable, Iterator

from wrapt import decorator


# TODO: short module description, purpose


__all__ = ['sampledict', 'bytewise', 'bitwise', 'deprecated', 'autorepr', 'typename', 'spy']



sampledict = {
    1: 'a',
    2: 'b',
    'None': None,
    'bool': True,
    'str': 'python',
    'multilineStr': '1st str' + '\n' + '2nd str',
    'ellipsis': ...,
    'list': [1, 2, 3, 4, 5, ('a', 'b', 'c'), ..., None],
    'dict': {1: 'first', 2: 'second'},
    'object': object(),
    'errorClass': RuntimeError,
    'function': print,
    'module': re,
}
sampledict['self'] = sampledict


def bytewise(byteseq: bytes, sep: str = ' ', limit: int = None, show_len: bool = True) -> str:
    """
    Return string representation of `byteseq` as hexadecimal uppercase octets separated by `sep`
    Functionally is the inverse of `bytes.fromhex()`
    In case the length of `byteseq` exceeds the value of specified `limit` argument, extra part of
        output is collapsed to an ellipsis and only the last element is shown after it (see example)
    If output is trimmed, `show_len` argument tells whether '(`<n>` bytes)' is appended to output
    >>> bytewise(b'12345', sep='-') == '31-32-33-34-35'
    >>> bytewise(bytes.fromhex('00 01 42 5A FF')) == '00 01 42 5A FF'
    >>> bytewise(b'python', limit=5) == '70 79 74 .. 6E (6 bytes)'
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
    >>> bitwise(b'abc') == '01100001 01100010 01100011'
    >>> bitwise(bytes.fromhex('00 0A FF')) == '00000000 00001010 11111111'
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


def typename(obj: Any) -> str:
    """Return simple name of the class of given object"""
    return obj.__class__.__name__


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
