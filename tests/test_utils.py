import string
from inspect import signature
from itertools import islice
from operator import itemgetter
from random import choices
from typing import NamedTuple, Iterator, Iterable, List, Callable, Dict

from pytest import fixture, mark, raises, warns, param

from utils.utils import bytewise, bitwise, deprecated, autorepr, spy, typename, Tree


class TestBytewise:

    patterns = (
        'general        00-42-FF-01-02-03-A0-0A',
        'all hex nums   01-23-45-67-89-AB-CD-EF',
        'single byte    CD',
        'zeros          00-00-00-00-00-00-00-00',
        'FFs            FF-FF-FF-FF-FF-FF-FF-FF',
        'empty          -',
    )

    patterns_limit = (
        'fits           AA-BB-CC-DD-EE    AA-BB-CC-DD-EE    6',
        'equals         AA-BB-CC-DD-EE    AA-BB-CC-DD-EE    5',
        'exceeds        AA-BB-CC-DD-EE    AA-BB-..-EE       4',
        'tree           AA-BB-CC-DD-EE    AA-..-EE          3',
        'two            AA-BB-CC-DD-EE    ..-EE             2',
        'one            AA                AA                2',
        'zero           -                 -                 2',
        'fits freely    AA-BB-CC-DD-EE    AA-BB-CC-DD-EE    999999',
        'two + equals   AA-BB             AA-BB             2',
    )

    @staticmethod
    def gen_ids(item: str):
        return item.split('  ', maxsplit=1)[0].strip()

    @fixture(scope='class', params=patterns, ids=gen_ids.__func__)
    def data_bytewise(self, request):
        result = ' '.join(request.param.split()[-1].split('-')).strip()
        operand = bytes.fromhex(result)
        return operand, result

    @fixture(scope='class', params=patterns_limit, ids=gen_ids.__func__)
    def data_bytewise_limit(self, request):
        *_, operand, result, limit = request.param.split()
        operand = bytes.fromhex(' '.join(operand.split('-')))
        result = '' if result == '-' else result.strip()
        limit = int(limit)
        return operand, result, limit

    def test_bytewise(self, data_bytewise):
        operand, expected = data_bytewise
        assert bytewise(operand) == expected

    @mark.parametrize('sep', (' ', '-', '_', ''), ids=repr)
    def test_bytewise_sep(self, data_bytewise, sep):
        operand, expected = data_bytewise
        expected = expected.replace(' ', sep)
        assert bytewise(operand, sep=sep) == expected

    def test_bytewise_limit(self, data_bytewise_limit):
        operand, expected, limit = data_bytewise_limit
        assert bytewise(operand, sep='-', limit=limit, show_len=False) == expected

    def test_bytewise_big(self):
        expected = ' '.join(''.join(choices('0123456789ABCDEF', k=2)) for _ in range(2**16+1))
        operand = bytes.fromhex(expected)
        assert bytewise(operand) == expected

    def test_bytewise_show_len(self):
        operand = bytes.fromhex(' '.join((f'{i:02X}' for i in range(256))))
        expected = '00 01 02 03 04 05 06 07 .. FF'
        assert bytewise(operand, limit=10, show_len=False) == expected
        assert bytewise(operand, limit=10) == expected + ' (256 bytes)'

    @mark.parametrize('limit', (1, 0, -1, -999, False, 's'))
    def test_bytewise_invalid(self, limit):
        exception = ValueError if isinstance(limit, int) else TypeError
        with raises(exception):
            bytewise(b'python', limit=limit)

    # TODO: add tests for bytearray


class TestBitwise:
    patterns = (
        'general        00-42-FF-01-02-03-A0-0A',
        'all hex nums   01-23-45-67-89-AB-CD-EF',
        'single byte    CD',
        'zeros          00-00-00-00-00-00-00-00',
        'FFs            FF-FF-FF-FF-FF-FF-FF-FF',
        'empty          -',
    )

    @fixture(scope='class', params=patterns, ids=TestBytewise.gen_ids)
    def data_bitwise(self, request):
        octets = request.param.split()[-1].split('-')
        operand = bytes.fromhex(' '.join(octets))
        result = ' '.join((bin(int(byte, base=16))[2:].rjust(8, '0') for byte in filter(None, octets)))
        return operand, result

    def test_bitwise(self, data_bitwise):
        operand, expected = data_bitwise
        assert bitwise(operand) == expected

    @mark.parametrize('sep', (' ', '-', '_', ''), ids=repr)
    def test_bitwise_sep(self, data_bitwise, sep):
        operand, expected = data_bitwise
        expected = expected.replace(' ', sep)
        assert bitwise(operand, sep=sep) == expected


class TestDeprecated:

    @staticmethod
    def get_func():
        """ Required to acquire pure function without bonding it to test class """
        def func(a: float, /, b: str, c: int = 0, *, d: bool, f=None):
            return f'{a=}, {b=}, {c=}, {d=}, {f=}'
        return func

    class Class:
        def __init__(self, *args, **kwargs):
            self.attr = ...

        def __eq__(self, other):
            return self.attr == other.attr

        def instancemethod(self, a: float, /, b: str, c: int = 0, *, d: bool, f=None):
            return f'{self=}, {a=}, {b=}, {c=}, {d=}, {f=}'

        @staticmethod
        def staticmethod(a: float, /, b: str, c: int = 0, *, d: bool, f=None):
            return f'{a=}, {b=}, {c=}, {d=}, {f=}'

        @classmethod
        def classmethod(cls, a: float, /, b: str, c: int = 0, *, d: bool, f=None):
            return f'{cls=}, {a=}, {b=}, {c=}, {d=}, {f=}'

        def __call__(self, a: float, /, b: str, c: int = 0, *, d: bool, f=None):
            return f'{self=}, {a=}, {b=}, {c=}, {d=}, {f=}'

    callables = (
        (get_func.__func__(), 'func'),
        (Class, 'class'),
        (Class.classmethod, 'classmethod'),
        (Class.staticmethod, 'staticmethod'),
        (Class().instancemethod, '.instancemethod'),
        (Class().classmethod, '.classmethod'),
        (Class().staticmethod, '.staticmethod'),
        (Class().__call__, 'class()'),
    )

    @fixture(scope='class', params=(None, '', 'reason'), ids='reason={}'.format)
    def data_reason(self, request):
        return request.param

    @fixture(scope='class', params=callables, ids=itemgetter(1))
    def data_deprecated(self, data_reason, request):
        args = (3.2, 'result=')
        kwargs = dict(d=True, f=Ellipsis)
        wrapee = request.param[0]
        if data_reason is None:
            wrapper = deprecated(wrapee)
        else:
            wrapper = deprecated(data_reason)(wrapee)
        return args, kwargs, data_reason, wrapee, wrapper

    def test_deprecated(self, data_deprecated):
        args, kwargs, reason, original, decorated = data_deprecated
        assert decorated.__wrapped__ == original
        message_pattern = rf'.*\({reason}\)' if reason else ''
        with warns(DeprecationWarning, match=message_pattern):
            assert decorated(*args, **kwargs) == original(*args, **kwargs)
        attrs = ('__name__', '__doc__', '__func__')
        equal = lambda attr: getattr(decorated, attr) == getattr(original, attr)
        assert all(equal for attr in attrs if hasattr(original, attr))
        assert signature(decorated) == signature(original)


class TestAutorepr:

    @fixture(scope='class')
    def data_autorepr(self):
        class A:
            attr = 'value'
            __repr__ = autorepr(f'class with attr={attr}')
        instance = A()
        qualname = '.'.join((self.__class__.__name__, 'data_autorepr', '<locals>', 'A'))
        message = "class with attr=value"
        return instance, qualname, message, id(instance)

    def test_autorepr(self, data_autorepr):
        instance, qualname, message, obj_id = data_autorepr
        assert repr(instance) == f'<{__name__}.{qualname} {message} at {hex(obj_id)}>'
        assert instance.__repr__.__name__ == '__repr__'
        assert instance.__repr__.__self__ == instance


class TestSpy:
    """
    Iterables: range object, tuple, dict, dict.items(), string
    Number of elements: 0, 1, 2, 3, 8, 90
    Lookahead depth: 1, 2, half of iterable, up to penultimate element, all
    • check lookahead:
        • wrap iterable in `spy()` object
        • advance `spy.lookahead()` iterator for N elements
        • check `spy` object and `spy.lookahead()` both conform to iterator protocol
        • check introspected elements being exactly the first N items from original iterable
        • check elements left in `spy.lookahead()` iterator being exactly the remaining items of original iterable
        • check `spy()` object itself gives the same items being iterated over as original iterable does
        • check both `spy()` and `spy.lookahead()` iterators are fully exhausted
    • check iterable is exhausted only if spy.lookahead() or original iterable is advanced
    • check nothing breaks if `spy.lookahead()` is attempted to be advanced beyond the size of the original iterable
    """

    IterableGen = Callable[[int], Iterable]

    class LookaheadTestcase(NamedTuple):
        spy: spy  # spy object wrapping the iterable
        lookahead: Iterator  # spy.lookahead() iterator, consumed to some point
        introspected: list  # items taken via lookahead
        k: int  # amount of elements introspected
        reference: list  # snapshot of original iterable contents

    sizes = [0, 1, 2, 3, 8, 80]
    iterable_generators: Dict[str, IterableGen] = {
        'range':      range,
        'tuple':      lambda n: tuple(range(n)),
        'dict':       lambda n: {str(i): i for i in range(n)},
        'dict.items': lambda n: {str(i): i for i in range(n)}.items(),
        'str':        lambda n: string.printable[:n],
    }

    @staticmethod
    def lookahead_params(sizes: List[int], generators: Dict[str, IterableGen]):
        """
        Generator of test parameters for `testcase` fixture
        Yields param(original iterable, lookahead depth, reference iterable snapshot)
        """

        for n in sizes:
            if n == 0:
                lookahead_depths = [0, 1]
            elif n > 5:
                lookahead_depths = [0, 1, n//2, n-2, n-1]
            else:
                lookahead_depths = range(n)
            for depth in lookahead_depths:
                for name, generator in generators.items():
                    yield param((generator(n), depth, list(generator(n))), id=f'{name}-{n}-{depth}')

    @staticmethod
    def overflow_params(sizes: List[int], generators: Dict[str, IterableGen]):
        """
        Generator of test parameters for `testcase` fixture
        Yields param(original iterable, lookahead depth, reference iterable snapshot)
        """
        for n in sizes:
            for name, generator in generators.items():
                yield param((generator(n), n+1, list(generator(n))), id=f'{name}-{n}')

    @fixture
    def lookahead_testcase(self, request):
        """
        Fixture to generate test cases for lookahead
        Yields (test node id, iterable size, spy object, advanced lookahead iterator, reference list)
        """
        iterable, depth, reference = request.param
        spy_object = spy(iterable)
        lookahead = spy_object.lookahead()
        introspected = list(islice(lookahead, depth))
        return self.LookaheadTestcase(spy_object, lookahead, introspected, depth, reference)

    @fixture(params=[range(8), list(range(8)), islice(range(10), 8)], ids=typename)
    def laziness_testcase(self, request):
        spy_object = spy(request.param)
        return spy_object, spy_object.lookahead()

    def test_doc(self):
        iterator = spy(range(1, 4))
        lookahead = iterator.lookahead()
        assert lookahead.__next__() == 1
        assert iterator.__next__() == 1
        assert list(lookahead) == [2, 3]
        assert list(iterator) == [2, 3]
        assert list(lookahead) == []

    @mark.parametrize('lookahead_testcase', lookahead_params.__func__(sizes, iterable_generators), indirect=True)
    def test_lookahead(self, lookahead_testcase):
        spy_object, lookahead, introspected, k, reference = lookahead_testcase
        for attr in '__next__', '__iter__':
            assert hasattr(spy_object, attr)
            assert hasattr(lookahead, attr)
        assert introspected == reference[:k]
        assert list(lookahead) == reference[k:]
        assert list(spy_object) == reference
        with raises(StopIteration):
            spy_object.__next__()
        with raises(StopIteration):
            lookahead.__next__()

    @mark.parametrize('lookahead_testcase', overflow_params.__func__(sizes, iterable_generators), indirect=True)
    def test_lookahead_overflow(self, lookahead_testcase):
        spy_object, lookahead, introspected, k, reference = lookahead_testcase
        assert introspected == reference
        assert list(lookahead) == []
        assert list(spy_object) == reference

    def test_laziness(self, laziness_testcase):
        spy_object, lookahead = laziness_testcase
        for i in range(4):
            item = lookahead.__next__()
            assert spy_object.__next__() is item
            assert spy_object.__next__() == item + 1
        with raises(StopIteration):
            spy_object.__next__()
        with raises(StopIteration):
            lookahead.__next__()


class TestTree:

    class Item:
        def __init__(self, name, children):
            self.name = name
            self.children = children
            self.invalid = 0

        def __str__(self):
            return self.name

        def get_children(self):
            return self.children

        @property
        def get_name(self):
            return self.name

    @fixture(scope='class', params=['children', Item.get_children],
             ids=['nodes=str', 'nodes=func'])
    def children_handle(self, request):
        return request.param

    @fixture(scope='class', params=['name', lambda item: item.name, 'get_name', str],
             ids=['name=str', 'name=func', 'name=prop', 'name=str'])
    def name_handle(self, request):
        return request.param

    @fixture(scope='class', params=['strict', 'smooth', 'indent'])
    def render_style(self, request):
        return request.param

    @fixture(scope='class')
    def root_item(self):
        c = self.Item('c', None)
        a = self.Item('a', None)
        b = self.Item('b', [c])
        d = self.Item('d', None)
        e = self.Item('e', [a, b, d])
        f = self.Item('f', [e])
        return f

    @fixture(scope='class')
    def testcase_linked_tree(self, name_handle, children_handle, render_style, root_item):
        rendered = {
            'strict': '''
                f
                └── e
                    ├── a
                    ├── b
                    │   └── c
                    └── d
                ''',
            'smooth': '''
                f
                ╰── e
                    ├── a
                    ├── b
                    │   ╰── c
                    ╰── d
                ''',
            'indent': '''
                f
                    e
                        a
                        b
                            c
                        d
                ''',
        }

        result = '\n'.join(line[4*4:] for line in rendered[render_style].splitlines() if line.strip())
        return Tree.get(root_item, name_handle, children_handle), result, render_style

    @fixture(scope='class', params=['<Empty tree>', ''], ids=['empty=default', 'empty=none'])
    def testcase_empty(self, request):
        result = request.param
        return Tree(None), result, request.param

    @fixture(scope='class')
    def testcase_single_item(self, name_handle, children_handle):
        item = self.Item('item', None)
        return Tree.get(item, name_handle, children_handle), 'item'

    def test_linked_tree(self, testcase_linked_tree):
        tree, rendered, style = testcase_linked_tree
        assert tree.render(style) == rendered

    def test_single_item_tree(self, testcase_single_item):
        tree, rendered = testcase_single_item
        assert str(tree) == rendered

    def test_empty_tree(self, testcase_empty):
        tree, rendered, empty_arg = testcase_empty
        assert tree.render(empty=empty_arg) == rendered

    def test_invalid_style(self, testcase_linked_tree):
        tree, rendered, style = testcase_linked_tree
        with raises(ValueError, match=r"invalid style: expected \[.*\], got 'wrong'"):
            tree.render('wrong')

    @mark.parametrize('children_handle', ['invalid'], indirect=True)
    def test_invalid_children_handle(self, name_handle, children_handle, root_item):
        err_msg = r"children handle returned invalid result: expected List\[Item\], got 0"
        with raises(RuntimeError, match=err_msg):
            Tree.get(root_item, name_handle, children_handle)
