from __future__ import annotations as _

import asyncio
from collections import defaultdict
from contextlib import contextmanager, asynccontextmanager
from enum import Enum
from functools import partial
from itertools import repeat, chain
from operator import itemgetter
from random import choices, randint, choice
from typing import *
from typing import IO, TextIO, BinaryIO, Pattern, Match
from typing import _GenericAlias as GenericAlias
from typing import _SpecialForm as SpecialForm
from typing import _type_check as typing_check_arg

from pytest import fixture, raises, fail, skip, mark
from wrapt import decorator

from utils.typechecking import _check_type_, TypecheckError, Typespec, NoneType, _format_type_, check_args


# CONSIDER: Call each typespec with all possible typeargs and just check no error except for TypecheckError is raised


# Type aliases
TestData = Tuple[Any, Typespec]  # value, typespec
ErrorData = Tuple[Any, Typespec, Type[Exception], str]  # value, typespec, raised_exception, error_message_pattern
Outcome = Literal['ok', 'fail']


# Constants
RECURSION_LIMIT: Final[int] = 3
DUMMY_RESULTS: Final[Dict[str, TestData]] = dict(ok=(42, int), fail=(0, str))


class Tester:
    # all tester classes under respectful name
    all: Dict[str, Type[Tester]] = {}

    # type unit being tested by each individual class
    typevar: Typespec = None

    # (obj, typespec) pairs valid/invalid to each individual unit
    ok: Tuple[TestData, ...] = ()
    fail: Tuple[TestData, ...] = ()
    err: Tuple[ErrorData, ...] = ()

    @classmethod
    def gen_ok(cls, data: Dict[str, TestData]) -> Iterator[TestData]:
        """Generator that yields valid (value, spec) pairs based on data iterator being passed to it"""
        raise NotImplementedError  # empty generator fallback implementation

    @classmethod
    def gen_fail(cls, data: Dict[str, TestData]) -> Iterator[TestData]:
        """Generator that yields invalid (value, spec) pairs based on data iterator being passed to it"""
        raise NotImplementedError  # empty generator fallback implementation

    def __init_subclass__(cls, **kwargs):
        cls.all[cls.__name__.strip('_')] = cls
        for name in 'ok', 'fail', 'err':
            attr = getattr(cls, name)
            if callable(attr):
                setattr(cls, name, tuple(attr()))
            else:
                setattr(cls, name, tuple(zip(attr, repeat(cls.typevar))))


def is_valid_typearg(typespec):
    try:
        typing_check_arg(typespec, msg='')
    except TypeError:
        return False
    else:
        return True


def gen_specs(outcome: Outcome, *, level=1) -> TestData:
    if level > RECURSION_LIMIT:
        yield DUMMY_RESULTS[outcome]
        return

    for tester in Tester.all.values():
        test_cases = getattr(tester, outcome)
        yield from ((obj, typespec) for obj, typespec in test_cases if is_valid_typearg(typespec))

    for tester in Tester.all.values():
        method = getattr(tester, f'gen_{outcome}')
        specs = dict(ok=list(gen_specs('ok', level=level + 1)), fail=list(gen_specs('fail', level=level + 1)))

        try:
            test_case_generator = method(specs)
        except NotImplementedError:
            continue

        for obj, typespec in test_case_generator:
            if is_valid_typearg(typespec):
                yield obj, typespec


# ————————————————————————————————————————————— Auxiliary classes / objects —————————————————————————————————————————— #

class E(Enum):
    A = 1
    B = 2


class SampleClass:
    def __repr__(self): return '<sample>'


class UniqueClass:
    def __repr__(self): return '<unique>'


class CallableClass:
    def __call__(self, *args, **kwargs): pass


class CM:
    def __enter__(self): return 42

    def __exit__(self, exc_type, exc_val, exc_tb): pass


class ACM:
    def __aenter__(self): return 42

    def __aexit__(self, exc_type, exc_val, exc_tb): pass


class G:
    def __iter__(self): yield 1

    def __next__(self): return 1

    def send(self): pass

    def throw(self): pass

    def close(self): pass


class AG:
    def __aiter__(self): yield 1

    def __anext__(self): return 1

    def asend(self): pass

    def athrow(self): pass

    def aclose(self): pass


class I:
    def __iter__(self): yield 1


class AI:
    def __aiter__(self): yield 1


@runtime_checkable
class SP(Protocol):
    def meth(self, a): pass


@runtime_checkable
class P(Protocol):
    attr: int = None

    def meth(self): pass


class TD(TypedDict, total=False):
    a: int
    b: str
    c: Union[float, Iterable]


class TTD(TypedDict, total=True):
    a: int
    b: str
    c: Union[float, Iterable]


class NT(NamedTuple):
    a: int
    b: str
    c: Union[float, Iterable]
    d: type = int
    e: bool = None


T = TypeVar('T')
TB = TypeVar('TB', bound=int)
TC = TypeVar('TC', str, type)
TT = TypeVar('TT', bound=TB)
TV = TypeVar('TV', bound=Union[int, Literal['t', 'v'], T])


class GN(Generic[TB]):
    attr = Type[TB]

    def meth(self, arg) -> TB: pass


def function(a): pass


async def coro(): pass


def gen(): yield 1


async def agen(): yield 1


@contextmanager
def cm():
    a = 42
    yield a
    return


@asynccontextmanager
async def acm():
    from asyncio import sleep
    a = 42
    await sleep(0)
    return


# ——————————————————————————————————————————————————————— Testers ———————————————————————————————————————————————————— #

class _NoneType_(Tester):
    typevar = NoneType
    ok = [None]
    fail = [1, NoneType]


class _Any_(Tester):
    typevar = Any
    ok = [1, Any, object, SampleClass()]


class _ClassVar_(Tester):
    @classmethod
    def err(cls):
        yield 42, ClassVar, TypeError, "bare ClassVar is invalid type specification"

    @classmethod
    def gen_ok(cls, data):
        yield from ((obj, ClassVar[typespec]) for obj, typespec in data['ok'])

    @classmethod
    def gen_fail(cls, data):
        yield from ((obj, ClassVar[typespec]) for obj, typespec in data['fail'])


class _Final_(Tester):
    @classmethod
    def err(cls):
        yield 42, Final, TypeError, "bare Final is invalid type specification"

    @classmethod
    def gen_ok(cls, data):
        yield from ((obj, Final[typespec]) for obj, typespec in data['ok'])

    @classmethod
    def gen_fail(cls, data):
        yield from ((obj, Final[typespec]) for obj, typespec in data['fail'])


class _Literal_(Tester):
    literals = 's', b'/x00', u'u', 42, 1.2e-9, 3j, True, False, None, E.A, E.B, 1, 2, 3

    @classmethod
    def ok(cls):
        yield 'a', Literal['a', 'b', 'c']
        yield 'a', Literal['a']
        yield 1, Literal[1]
        yield 1, Literal[1, 2, 3]
        for i in range(10):
            sample = choices(cls.literals, k=randint(1, 10))
            yield choice(sample), Literal[tuple(sample)]

    @classmethod
    def fail(cls):
        yield 'd', Literal['a', 'b', 'c']
        yield 'c', Literal['a']
        yield 2, Literal[1]
        yield 5, Literal[1, 2, 3]
        yield '1', Literal[1, 2, 3]
        for i in range(10):
            sample = choices(cls.literals, k=randint(1, 10))
            yield 'invalid', Literal[tuple(sample)]

    @classmethod
    def err(cls):
        yield 42, Literal, TypeError, "bare Literal is invalid type specification"


class _Optional_(Tester):
    @classmethod
    def ok(cls):
        yield None, Optional[int]
        yield 1, Optional[int]
        yield 1, Optional[Optional[int]]

    @classmethod
    def fail(cls):
        yield 1, Optional[str]
        yield 1, Optional[Optional[str]]

    @classmethod
    def err(cls):
        yield 42, Optional, TypeError, "bare Optional is invalid type specification"

    @classmethod
    def gen_ok(cls, data):
        yield from ((obj, Optional[typespec]) for obj, typespec in data['ok'])
        yield from ((None, Optional[typespec]) for obj, typespec in data['ok'])


class _Union_(Tester):
    @classmethod
    def ok(cls):
        yield 0, Union[int]
        yield 1, Union[(int,) * 10]
        yield 2, Union[int, str]
        yield KeyError(), Union[LookupError, int]
        yield bool, Union[Type[int], Type[str]]
        yield None, Union[None, None, int]
        yield 42, Union[object, str]

    @classmethod
    def fail(cls):
        yield 0, Union[str]
        yield 1, Union[(str,) * 10]
        yield 2, Union[float, str]
        yield ValueError(), Union[LookupError, int]
        yield int, Union[Type[float], Type[str]]
        yield 1.0, Union[None, None, int]
        yield str, Union[bytes, str]

    @classmethod
    def err(cls):
        yield 42, Union, TypeError, "bare Union is invalid type specification"

    @classmethod
    def gen_ok(cls, data):
        yield from ((obj, Union[UniqueClass, typespec]) for obj, typespec in data['ok'])
        yield from ((1, Union[int, typespec]) for obj, typespec in data['ok'])
        yield 42, Union[tuple(typespec for obj, typespec in data['ok'])]

    @classmethod
    def gen_fail(cls, data):
        for obj, typespec in data['fail']:
            different_type = str if isinstance(obj, int) else int
            yield obj, Union[different_type, typespec]


class _Awaitable_(Tester):
    typevar = Awaitable
    ok = [coro(), asyncio.sleep(1), asyncio.Task(coro()), asyncio.Future()]
    fail = [coro, print, 1, None, asyncio.Future]


class _Coroutine_(Tester):
    typevar = Coroutine
    ok = [coro(), asyncio.sleep(1)]
    fail = [coro, function, 42, None, asyncio.Future, asyncio.Task(coro()), asyncio.Future()]


class _Callable_(Tester):
    typevar = Callable
    ok = [print, function, str.split, bytes.fromhex, partial(print, ''), SampleClass, CallableClass(), int]
    fail = [42, None, coro(), {}]


class _ContextManager_(Tester):
    typevar = ContextManager
    ok = [cm(), CM()]
    fail = [acm(), ACM(), None, function, coro()]


class _AsyncContextManager_(Tester):
    typevar = AsyncContextManager
    ok = [acm(), ACM()]
    fail = [cm(), CM(), None, function, coro()]


class _Generator_(Tester):
    typevar = Generator
    ok = [gen(), (id(i) for i in range(1)), G()]
    fail = [range(1), print, G, I(), AG(), None]


class _AsyncGenerator_(Tester):
    typevar = AsyncGenerator
    ok = [agen(), AG()]
    fail = [G(), I(), coro(), AG, None]


class _Hashable_(Tester):
    typevar = Hashable
    ok = [1, 's', True, (1, 2), function, int, coro(), SampleClass, range(1), b'b']
    fail = [{}, type('UH', (), {'__eq__': lambda _: None})()]


class _Iterable_(Tester):
    typevar = Iterable
    ok = ['str', I(), range(1), G()]
    fail = [1, None, coro()]


class _AsyncIterable_(Tester):
    typevar = AsyncIterable
    ok = [agen(), AI(), ]
    fail = [1, None, coro(), asyncio.sleep(0)]


class _Iterator_(Tester):
    typevar = Iterator
    ok = [iter(range(1)), iter('s'), enumerate('s')]
    fail = [I(), range(1), [1, 2, 3], coro(), None]


class _Reversible_(Tester):
    typevar = Reversible
    ok = [[], 's', {}, range(1)]
    fail = [set(), I(), iter('s'), None]


class _Sized_(Tester):
    typevar = Sized
    ok = [[], 's', {}, range(1), set()]
    fail = [I(), iter('s'), None]


class _SupportsRound_(Tester):
    typevar = SupportsRound
    ok = [1, 1.0]
    fail = [set(), I(), iter('s'), None]


class _Dict_(Tester):
    """Represents all container types"""
    typevar = Dict
    ok = [{}, {1: 's', 'a': 'o'}, defaultdict(set)]
    fail = [SampleClass.__dict__, [], None]


class _Tuple_(Tester):

    @classmethod
    def ok(cls):
        yield (), Tuple
        yield (1, 2, 3), Tuple
        yield ('s', None, 1.0), Tuple
        yield (), Tuple[int, ...]
        yield (1, 2, 3), Tuple[int, ...]
        yield (1, 2, 3), Tuple[str, ...]  # type is not checked in homogeneous Tuples
        yield ('s', None, 1.0), Tuple[Any, ...]
        yield (1,), Tuple[int]
        yield (1, 2, 3), Tuple[int, int, int]
        yield (SampleClass(), int, 's'), Tuple[SampleClass, type, Iterable]
        yield (...,), Tuple[type(Ellipsis)]

    @classmethod
    def fail(cls):
        yield [], Tuple
        yield [1, 2, 3], Tuple[int, ...]
        yield (1,), Tuple[str]
        yield (1, 2, 3), Tuple[int, int, float]
        yield (1, None), Tuple[int, int]
        yield (1, 's', None), Tuple[int, str]

    @classmethod
    def gen_ok(cls, data):
        for obj, typespec in data['ok']:
            yield (obj,), Tuple[typespec]
        for obj, typespec in data['ok']:
            yield (obj, SampleClass()), Tuple[typespec, SampleClass]
        objs, typespecs = zip(*data['ok'])
        yield tuple(objs), Tuple[tuple(typespecs)]

    @classmethod
    def gen_fail(cls, data):
        for obj, typespec in data['fail']:
            yield (obj,), Tuple[typespec]
        for obj, typespec in data['fail']:
            yield (obj, SampleClass()), Tuple[typespec, SampleClass]
        objs, typespecs = zip(*data['ok'])
        yield tuple(objs[1:]), Tuple[tuple(typespecs)]


class _Protocol_(Tester):
    @classmethod
    def ok(cls):
        yield int, Protocol
        yield P, P
        yield type('TP', (), {'attr': P.attr, 'meth': P.meth})(), P
        yield type('TP', (), {'attr': P.attr, 'meth': P.meth, 'extra': 0})(), P
        yield type('TP2', (), {'attr': 'a', 'meth': lambda self: None})(), P
        yield type('STP', (), {'meth': lambda self: None})(), SP

    @classmethod
    def fail(cls):
        values = (
            None,
            type('TP_F', (), {'attr': 'a', 'meth': None})(),
            type('TP_F', (), {'attr': 'a', 'meth_f': None})(),
            type('TP_F', (), {'attr_f': 'a', 'meth': lambda self: None})(),
        )
        yield from zip(values, repeat(P))


class _Generic_(Tester):
    @classmethod
    def ok(cls):
        yield GN(), Generic
        yield GN(), GN
        yield GN(), GN[int]  # arguments are not checked
        yield GN(), GN[T]  # arguments are not checked

    @classmethod
    def fail(cls):
        yield None, Generic
        yield Generic, Generic
        yield GN, Generic
        yield int, GN
        yield Dict, GN


class _TypedDict_(Tester):
    @classmethod
    def ok(cls):
        yield dict(a=1, b='s', c=1.0), TD
        yield dict(a=1, b='s', c=1.0), TTD
        yield dict(a=1, b='s', c=[]), TTD
        yield dict(a=True, b=u's', c='iterable'), TD
        yield dict(a=1, b='s'), TD
        yield dict(), TD

    @classmethod
    def fail(cls):
        yield None, TD
        yield (), TD
        yield [], TTD
        yield {}, TTD
        yield dict(a=1, b='s'), TTD
        yield dict(a=1, b='s', c=1.0, d='extra'), TD
        yield dict(a=1, b='s', c=1.0, d='extra'), TTD
        dict(a=1, b='s', c=1), TD
        dict(a=1, b=None), TD

    @classmethod
    def err(cls):
        yield {}, TypedDict, TypeError, 'bare TypedDict does not support typechecking'


class _NamedTuple_(Tester):
    nt = NT(a=1, b='s', c=1.0)
    full_nt = NT(a=2, b='ss', c=[1, 2, 3], d=str, e=False)
    FakeNT = type('FakeNT', (), {'_fields': (), '_field_defaults': ()})

    @classmethod
    def ok(cls):
        yield cls.nt, NT
        yield cls.full_nt, NT
        yield cls.nt, NamedTuple
        yield cls.full_nt, NamedTuple

    @classmethod
    def fail(cls):
        yield None, NT
        yield SampleClass(), NT
        yield SampleClass, NamedTuple
        yield tuple, NamedTuple
        yield (1, 's', 1.0), NT
        yield cls.FakeNT(), NT
        yield cls.FakeNT, NamedTuple


class _TypeVar_(Tester):
    values = (None, 1, [], SampleClass(), coro(), type, print, T, zip, Any)

    @classmethod
    def ok(cls):
        yield from zip(cls.values, repeat(T))
        yield 1, TB
        yield True, TB
        yield 's', TC
        yield int, TC
        yield type, TC
        yield 0, TT
        yield -1, TV
        yield 'v', TV
        yield T, TV

    @classmethod
    def fail(cls):
        yield 's', TB
        yield None, TB
        yield TB, TB
        yield 0, TC
        yield [], TT


class _Pattern_(Tester):
    import re

    @classmethod
    def ok(cls):
        yield cls.re.compile(r''), Pattern
        yield cls.re.compile(r''), Pattern[str]
        yield cls.re.compile(rb''), Pattern[bytes]
        yield cls.re.compile(r''), Pattern[TC]

    @classmethod
    def fail(cls):
        yield 'bare_str', Pattern
        yield cls.re.compile(rb''), Pattern[str]
        yield cls.re.compile(r''), Pattern[bytes]
        yield cls.re.compile(r''), Pattern[int]
        yield cls.re.compile(r''), Pattern[TB]

    @classmethod
    def gen_ok(cls, data):
        for obj, typespec in data['ok']:
            if isinstance(obj, (str, bytes)):
                yield cls.re.compile(obj), Pattern[typespec]

    @classmethod
    def gen_fail(cls, data):
        for obj, typespec in data['fail']:
            if isinstance(obj, (str, bytes, cls.re.Pattern)):
                yield cls.re.compile(obj), Pattern[typespec]


class _Match_(Tester):
    import re
    match_str = re.match('', '')
    match_bytes = re.match(b'', b'')

    @classmethod
    def ok(cls):
        yield cls.match_str, Match
        yield cls.match_str, Match[str]
        yield cls.match_bytes, Match[bytes]
        yield cls.match_str, Match[TC]

    @classmethod
    def fail(cls):
        yield None, Match
        yield None, Match[str]
        yield 'bare_str', Match
        yield 'bare_str', Match[str]
        yield cls.match_bytes, Match[str]
        yield cls.match_str, Match[bytes]
        yield cls.match_str, Match[int]

    @classmethod
    def gen_ok(cls, data):
        for obj, typespec in data['ok']:
            if isinstance(obj, str):
                yield cls.re.match('', obj), Match[typespec]
            elif isinstance(obj, bytes):
                yield cls.re.match(b'', obj), Match[typespec]

    @classmethod
    def gen_fail(cls, data):
        for obj, typespec in data['fail']:
            if isinstance(obj, str):
                yield cls.re.match('', obj), Match[typespec]
            elif isinstance(obj, bytes):
                yield cls.re.match(b'', obj), Match[typespec]


class _IO_(Tester):
    import sys
    fdt = sys.stderr
    fdb = open(sys.executable, 'rb')

    @classmethod
    def ok(cls):
        yield cls.fdt, IO
        yield cls.fdt, TextIO
        yield cls.fdb, IO
        yield cls.fdb, BinaryIO

    @classmethod
    def fail(cls):
        yield cls.fdt, BinaryIO
        yield cls.fdb, TextIO
        yield None, IO
        yield 1, IO
        yield 's', IO
        yield None, BinaryIO
        yield None, TextIO


class _Type_(Tester):

    @staticmethod
    def filter_args(args) -> bool:
        typespec = args[1]
        if isinstance(typespec, GenericAlias) and isinstance(typespec.__origin__, SpecialForm):
            return False
        if isinstance(typespec, TypeVar):
            return False
        if typespec in (Protocol, TypedDict, TD, TTD, SP, P):
            return False
        return True

    @classmethod
    def ok(cls):
        yield int, Type
        yield int, Type[int]
        yield bool, Type[int]  # subclass
        yield type, Type[type]
        yield type, Type[Type]
        yield type(TypedDict), Type[type]  # metaclasses should typecheck here as well
        yield NoneType, Type[None]  # None will be converted to NoneType
        yield NoneType, Type[NoneType]
        yield type(TypedDict), Type[Any]
        yield SP, Type[SP]
        yield type('STP', (), {'meth': lambda self: None}), Type[SP]
        yield NamedTuple, Type[NamedTuple]
        yield NT, Type[NamedTuple]
        yield NT, Type[NT]
        yield dict, Type[Dict]
        yield NT, Type[tuple]

    @classmethod
    def fail(cls):
        yield 0, Type
        yield 0, Type[int]
        yield type(TypedDict), Type[str]
        yield int, Type[type]
        yield List, Type[list]
        yield int, Type[str]
        yield None, Type[None]
        yield None, Type[NoneType]
        yield 0, Type[Any]
        yield int, Type[SP]
        yield type('STP', (), {'wrong': lambda self: None}), Type[SP]
        yield type('STP', (), {'meth': None}), Type[SP]
        yield tuple, Type[NamedTuple]
        yield cls.all['NamedTuple'].nt, Type[NamedTuple]
        yield NamedTuple, Type[NT]
        # do not even try treat TypeVar bound types or constraints as anchors for typechecking
        # TypeVar object is simply not a type and thus Type[T] is an error
        yield T, Type[TypeVar]
        yield int, Type[TypeVar]

    @classmethod
    def err(cls):
        yield P, Type[P], TypeError, "Protocols with non-method members don't support issubclass()"
        yield TD, Type[TypedDict], TypeError, "TypedDict does not support instance and class checks"
        yield TTD, Type[TTD], TypeError, "TypedDict does not support instance and class checks"
        yield int, Type[Union[int, str]], TypeError, r"type argument '.*' is not a type"
        yield str, Type[T], TypeError, r"type argument '.*' is not a type"

    @classmethod
    def gen_ok(cls, data):
        for obj, typespec in data['ok']:
            yield type(obj), Type[Any]
        for obj, typespec in filter(cls.filter_args, data['ok']):
            yield type(obj), Type[typespec]


# ———————————————————————————————————————————————————— Fixtures —————————————————————————————————————————————————————— #

@fixture(scope='module')
def spec_data():
    return dict(ok=list(gen_specs('ok')), fail=list(gen_specs('fail')))


@fixture(scope='module', params=tuple(chain(*(tester.ok for tester in Tester.all.values()))),
         ids='{0[0]}-{0[1]}-ok'.format)
def ok_data(request):
    return request.param


@fixture(scope='module', params=tuple(chain(*(tester.fail for tester in Tester.all.values()))),
         ids='{0[0]}-{0[1]}-fail'.format)
def fail_data(request):
    return request.param


@fixture(scope='module', params=tuple(chain(*(tester.err for tester in Tester.all.values()))),
         ids='{0[0]}-{0[1]}-err'.format)
def err_data(request):
    return request.param


@fixture(scope='module', params=Tester.all.values(), ids=(f'{name}-dynamic-ok' for name in Tester.all.keys()))
def dynamic_ok_data(request, spec_data):
    try:
        return request.param.gen_ok(spec_data)
    except NotImplementedError:
        skip(f"No dynamic pass-test for class {request.param.__name__}")


@fixture(params=Tester.all.values(), ids=(f'{name}-dynamic-fail' for name in Tester.all.keys()))
def dynamic_fail_data(request, spec_data):
    try:
        return request.param.gen_fail(spec_data)
    except NotImplementedError:
        skip(f"No dynamic failure-test for class {request.param.__name__}")


# ———————————————————————————————————————————————————————— Tests ————————————————————————————————————————————————————— #

def test_static_ok(ok_data):
    value, spec = ok_data
    _check_type_(value, spec, argname='<test>')


def test_static_fail(fail_data):
    value, spec = fail_data
    with raises(TypecheckError):
        _check_type_(value, spec, argname='<test>')
        fail(f"DID NOT RAISE TypecheckError with '{value}' against '{_format_type_(spec)}'")


def test_static_err(err_data):
    value, spec, error, pattern = err_data
    with raises(error, match=pattern):
        _check_type_(value, spec, argname='<test>')


@mark.slow
def test_dynamic_ok(dynamic_ok_data):
    for value, spec in dynamic_ok_data:
        _check_type_(value, spec, argname='<test>')


@mark.slow
def test_dynamic_fail(dynamic_fail_data):
    for value, spec in dynamic_fail_data:
        with raises(TypecheckError):
            _check_type_(value, spec, argname='<test>')
            fail(f"DID NOT RAISE TypecheckError with '{value}' against '{_format_type_(spec)}'")


def test_forward_ref():
    message = "ForwardRefs are not allowed. All annotations are expected to be resolved"
    with raises(TypeError, match=message):
        _check_type_(42, ForwardRef('Name'), argname='<test>')


# —————————————————————————————————————————————— @check_args() decorator ————————————————————————————————————————————— #

class TestCheckArgs:
    import re

    @staticmethod
    def case_simple_function():
        def func(a: Literal[1, 2]):
            pass
        return func

    @staticmethod
    def case_function():
        def func(a: int, b: str, c: float):
            pass
        return func

    class A:
        def __init__(self, a: int = 0, b: str = 's', c: float = 2.5):
            pass

        def __call__(self, a: int, b: str, c: float):
            pass

        def case_method(self, a: int, b: str, c: float):
            pass

        def case_method_pos_kw(self, a: int, /, b: str, *, c: float):
            pass

        @classmethod
        def case_class_method(cls, a: int, b: str, c: float = 0.0):
            pass

        @staticmethod
        def case_static_method(a: int = 0, b: str = 's', c: float = 2.5):
            pass

        def case_arbitrary_self(wrong, a: int, b: str, c: float):
            pass

        class B:
            def meth(self, a: int, b: str, c: float):
                pass

    @fixture(scope='class', params=[None, '', 'a', 'a,', 'a,a', ['a'], 'a,b', 'a, b', ['a', 'b'], 'a,b,c'], ids=str)
    def argnames(self, request):
        return request.param

    callables_data = [
        ('function', (0, 's', 2.5), {}, case_function.__func__()),
        ('method', (0, 's', 2.5), {}, A().case_method),
        ('method_kw', (), dict(a=0, b='s', c=2.5), A().case_method),
        ('invalid_bound_method', (0, 's', 2.5), {}, A.__dict__['case_method'].__get__(object)),
        ('pos_kw_method', (0, 's'), {'c': 2.5}, A().case_method_pos_kw),
        ('classmethod', (0, 's', 2.5), {}, A.case_class_method),
        ('staticmethod', (0, 's', 2.5), {}, A.case_static_method),
        ('init', (0, 's', 2.5), {}, A().__init__),
        ('call', (0, 's', 2.5), {}, A().__call__),
        ('arbitrary_self', (0, 's', 2.5), {}, A().case_arbitrary_self),
        ('inner_class_method', (0, 's', 2.5), {}, A.B().meth),
    ]

    @fixture(scope='class', params=callables_data, ids=itemgetter(0))
    def case(self, request, argnames):
        name, args, kwargs, func = request.param
        check_args_decorator = check_args if argnames is None else check_args(argnames)
        return name, args, kwargs, check_args_decorator(func)

    @fixture(scope='class')
    def case_fail(self, case):
        name, args, kwargs, func = case
        if kwargs:
            if 'a' not in kwargs.keys():
                skip("No keyword argument 'a' involved")
            new_kwargs = kwargs.copy()
            new_kwargs['a'] = None
            kwargs = new_kwargs
        else:
            args = (None, *args[1:])
        return name, args, kwargs, func

    @fixture(scope='class')
    def case_decorator(self, argnames):
        @check_args(argnames)
        def dec(a: int, b: str, c: float):
            @decorator
            def wrapper(func, instance, args, kwargs):
                return func(*args, **kwargs)
            return wrapper
        return dec

    @fixture(scope='class')
    def case_property(self, argnames):
        class ClassWithProperty:
            @property
            def prop(self):
                return 42

            @prop.setter
            @check_args(argnames)
            def prop(self, value: Union[Iterable, int]):
                pass
        return ClassWithProperty()

    @fixture(scope='class', params=['x', 'a,x', ['a', 'x'], 'x, x'], ids=str)
    def case_invalid_argnames(self, request):
        def func(a: int):
            pass
        return check_args(request.param), func

    @fixture(scope='class')
    def case_forward_ref(self):
        @check_args
        def case_fref(a: TestCheckArgs.A):
            pass
        return case_fref

    def test_simple(self):
        func = check_args(None)(self.case_simple_function())
        func(1)

    def test_simple_fail(self):
        func = check_args('a')(self.case_simple_function())
        error_msg = self.re.escape(r"argument 'a': None does not match any value from Literal[1, 2]")
        with raises(TypecheckError, match=error_msg):
            func(None)

    def test_pass(self, case):
        name, args, kwargs, func = case
        func(*args, **kwargs)

    def test_fail(self, case_fail):
        name, args, kwargs, func = case_fail
        with raises(TypecheckError, match="argument 'a': None is not int"):
            func(*args, **kwargs)

    def test_doc(self):
        annotation = r'Union[int, Dict[str, int], Tuple[Any, str]]'
        error_message = r"{} does not match any type specification from " + annotation

        @check_args
        def func(a: Union[int, Dict[str, int], Tuple[Any, str]]):
            pass

        for arg in (1, True, {}, {1: True, 2: 's'}, (object, 's')):
            func(arg)
        for arg in (None, ('s', 0), (0, 's', 'extra')):
            with raises(TypecheckError, match=self.re.escape(error_message.format(arg))):
                func(arg)

        @check_args('a, b')
        def func(a: Any, b: int, c: bool):
            ...

        func(object, 1, 's')

    def test_decorator(self, case_decorator):
        dec = case_decorator(1, 's', 2.5)
        wrapee = dec(min)
        assert wrapee(-1, 3) == -1

    def test_decorator_fail(self, case_decorator):
        with raises(TypecheckError, match="argument 'a': None is not int"):
            case_decorator(None, [], 3)

    @mark.parametrize('argnames', [None, '', 'value', 'value,'], indirect=True)
    def test_property(self, case_property, argnames):
        case_property.prop = 's'

    @mark.parametrize('argnames', [None, '', 'value', 'value, '], indirect=True)
    def test_property_fail(self, case_property, argnames):
        case_property.prop = ()

    def test_invalid_argnames(self, case_invalid_argnames):
        dec, func = case_invalid_argnames
        with raises(ValueError, match=r"non-existent argument name 'x'"):
            dec(func)

    def test_forward_refs(self, case_forward_ref):
        case_forward_ref(self.A())
