from string import printable
from inspect import signature
from itertools import islice
from operator import itemgetter
from random import choices
from typing import NamedTuple, Iterator, Iterable, List, Callable, Dict

from pytest import fixture, mark, raises, warns, param
from pytest import lazy_fixture

from utils.utils import bytewise, bitwise, deprecated, autorepr, spy, typename, Tree, AttrEnum


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
        'str':        lambda n: printable[:n],
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
        def __init__(self, name, children=None, parent=None):
            self.name = name
            self.children = children or []
            self.parent = parent
            self.invalid = 0

        def __str__(self):
            return self.name

        def get_children(self):
            return self.children

        @property
        def get_name(self):
            return self.name

    @staticmethod
    def strip_indents(string: str, n: int):
        return '\n'.join(line[4 * n:] for line in string.splitlines() if line.strip())

# ————————————————————————————————————————————————————— Fixtures ————————————————————————————————————————————————————— #

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

    @fixture(scope='class', params=['<Empty tree>', ''], ids=['empty=default', 'empty=none'])
    def empty_arg(self, request):
        return request.param

    @fixture(scope='class', params=['normal', 'reversed', 'top-down', 'bottom-up', 'random'])
    def items_order(self, request):
        return request.param

    @fixture(scope='class')
    def root_item(self):
        """Root item with children references, entailing all child nodes"""
        c = self.Item('c', None)
        a = self.Item('a', None)
        b = self.Item('b', [c])
        d = self.Item('d', None)
        e = self.Item('e', [a, b, d])
        f = self.Item('f', [e])
        return f

    @fixture(scope='class')
    def testcase_simple_tree(self, name_handle, children_handle, render_style, root_item):
        """Tree with children references: (Tree() object, tree representation string, render style used)"""

        representation = {
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

        tree = Tree.convert(root_item, name_handle, children_handle)
        return tree, self.strip_indents(representation[render_style], 4), render_style

    @fixture(scope='class')
    def testcase_empty_tree(self, empty_arg):
        """Tree with an empty root: (Tree() object, empty tree representation string, 'empty' argument)"""
        result = empty_arg
        return Tree(None), result, empty_arg

    @fixture(scope='class')
    def testcase_single_item_tree(self, name_handle, children_handle):
        """Tree of with 1 single node: (Tree() object, rendered tree string)"""
        item = self.Item('item', None)
        return Tree.convert(item, name_handle, children_handle), 'item'

    @fixture(scope='class')
    def testcase_tree_items(self, items_order):
        """Items with parent references: (list of items, rendered tree string)"""

        from random import sample
        from re import findall

        representation = '''
            Item01_level0
            ├── Item02_level1
            ├── Item03_level1
            │   └── Item04_level2
            │       └── Item05_level3
            │           └── Item06_level4
            ├── Item07_level1
            │   ├── Item08_level2
            │   │   ├── Item09_level3
            │   │   └── Item10_level3
            │   └── Item11_level2
            │       ├── Item12_level3
            │       └── Item13_level3
            └── Item14_level1
                ├── Item15_level2
                └── Item16_level2
                    ├── Item17_level3
                    └── Item18_level3
                        ├── Item19_level4
                        └── Item20_level4
        '''

        tree_orders = {
            'normal': range(20),
            'reversed': reversed(range(20)),
            'top-down': [0, 1, 2, 6, 13, 3, 7, 10, 14, 15, 4, 8, 9, 11, 12, 16, 17, 5, 18, 19],
            'bottom-up': reversed([0, 1, 2, 6, 13, 3, 7, 10, 14, 15, 4, 8, 9, 11, 12, 16, 17, 5, 18, 19]),
            'random': sample(list(range(20)), 20),
        }

        # Create items taking names from representation
        item_names = findall(r'Item\d*_level\d*', representation)
        items = [self.Item(name) for name in item_names]

        # Create links to parents
        items[1].parent = items[0]
        items[2].parent = items[0]
        items[3].parent = items[2]
        items[4].parent = items[3]
        items[5].parent = items[4]
        items[6].parent = items[0]
        items[7].parent = items[6]
        items[8].parent = items[7]
        items[9].parent = items[7]
        items[10].parent = items[6]
        items[11].parent = items[10]
        items[12].parent = items[10]
        items[13].parent = items[0]
        items[14].parent = items[13]
        items[15].parent = items[13]
        items[16].parent = items[15]
        items[17].parent = items[15]
        items[18].parent = items[17]
        items[19].parent = items[17]

        # Reorder items
        items = [items[i] for i in tree_orders[items_order]]

        return items, self.strip_indents(representation, 3)

    @fixture(scope='class')
    def testcase_exception_tree_items(self):
        import builtins

        representation = '''
            object
            └── BaseException
                ├── Exception
                │   ├── ArithmeticError
                │   │   ├── FloatingPointError
                │   │   ├── OverflowError
                │   │   └── ZeroDivisionError
                │   ├── AssertionError
                │   ├── AttributeError
                │   ├── BufferError
                │   ├── EOFError
                │   ├── ImportError
                │   │   └── ModuleNotFoundError
                │   ├── LookupError
                │   │   ├── IndexError
                │   │   └── KeyError
                │   ├── MemoryError
                │   ├── NameError
                │   │   └── UnboundLocalError
                │   ├── OSError
                │   │   ├── BlockingIOError
                │   │   ├── ChildProcessError
                │   │   ├── ConnectionError
                │   │   │   ├── BrokenPipeError
                │   │   │   ├── ConnectionAbortedError
                │   │   │   ├── ConnectionRefusedError
                │   │   │   └── ConnectionResetError
                │   │   ├── FileExistsError
                │   │   ├── FileNotFoundError
                │   │   ├── InterruptedError
                │   │   ├── IsADirectoryError
                │   │   ├── NotADirectoryError
                │   │   ├── PermissionError
                │   │   ├── ProcessLookupError
                │   │   └── TimeoutError
                │   ├── ReferenceError
                │   ├── RuntimeError
                │   │   ├── NotImplementedError
                │   │   └── RecursionError
                │   ├── StopAsyncIteration
                │   ├── StopIteration
                │   ├── SyntaxError
                │   │   └── IndentationError
                │   │       └── TabError
                │   ├── SystemError
                │   ├── TypeError
                │   ├── ValueError
                │   │   └── UnicodeError
                │   │       ├── UnicodeDecodeError
                │   │       ├── UnicodeEncodeError
                │   │       └── UnicodeTranslateError
                │   └── Warning
                │       ├── BytesWarning
                │       ├── DeprecationWarning
                │       ├── FutureWarning
                │       ├── ImportWarning
                │       ├── PendingDeprecationWarning
                │       ├── ResourceWarning
                │       ├── RuntimeWarning
                │       ├── SyntaxWarning
                │       ├── UnicodeWarning
                │       └── UserWarning
                ├── GeneratorExit
                ├── KeyboardInterrupt
                └── SystemExit
        '''

        isexception = lambda item: isinstance(item, type) and issubclass(item, BaseException)
        exceptions = [item for item in vars(builtins).values() if isexception(item)]
        rendered = '\n'.join(line[4 * 3:] for line in representation.splitlines() if line.strip())
        return exceptions, rendered

    @fixture(scope='class')
    def testcase_empty_tree_items(self, empty_arg):
        """Empty collection of items: (empty list, empty tree representation string)"""
        return [], empty_arg

    @fixture(scope='class')
    def testcase_single_item_tree_items(self):
        """Single item with parent reference: (list of 1 item, tree representation string)"""
        return [self.Item('single', parent=None)], 'single'

    @fixture(scope='class')
    def testcase_star_layout_tree_items(self):
        """Items with back references to a single root item: (list of items, tree representation string)"""
        representation = '''
            root
            ├── item1
            ├── item2
            ├── item3
            ├── item4
            └── item5
        '''
        root = self.Item('root')
        children = [self.Item(f'item{i}', parent=root) for i in range(1, 6)]
        return [root, *children], self.strip_indents(representation, 3)

    @fixture(scope='class')
    def testcase_chain_layout_tree_items(self):
        """Items linked together like backreference queue: (list of items, tree representation string)"""
        representation = '''
            item0
            └── item1
                └── item2
                    └── item3
                        └── item4
                            └── item5
        '''
        items = [self.Item(f'item{i}') for i in range(6)]
        for i in range(1, 6):
            items[i].parent = items[i-1]

        return items, self.strip_indents(representation, 3)

    @fixture(scope='class', params=[(0,), (0, 2, 3, 4), (3, 7, 10, 15)], ids=['root', 'branch', 'level2'])
    def testcase_missing_tree_items(self, request, testcase_tree_items):
        """Items with parent references with some parent items missing: (list of items, tree representation string"""
        items, representation = testcase_tree_items
        filtered_items = [items[i] for i in range(len(items)) if i not in request.param]
        return filtered_items, representation

    @fixture(scope='class')
    def testcase_multiple_roots_tree_items(self, testcase_tree_items):
        """Items with cycle references: list of items"""
        items, representation = testcase_tree_items
        second_root = self.Item('item21_2nd_root')
        child = self.Item('item22_2nd_root', parent=second_root)
        separate_branch_items = [second_root, child]
        return separate_branch_items + items

    @fixture(scope='class')
    def testcase_cycle_references_tree_items(self, testcase_exception_tree_items):
        """Items with cycle references: list of items"""
        items, representation = testcase_exception_tree_items
        # ▼ evil modification - now 'items' should no longer constitute a tree structure
        items[0].parent = items[50]
        return items

# —————————————————————————————————————————————————————— Tests ——————————————————————————————————————————————————————— #

    def test_render_linked(self, testcase_simple_tree):
        tree, rendered, style = testcase_simple_tree
        print('', tree.render(style), sep='\n')
        assert tree.render(style) == rendered

    def test_render_single_item(self, testcase_single_item_tree):
        tree, rendered = testcase_single_item_tree
        print('', tree, sep='\n')
        assert str(tree) == rendered

    def test_render_empty(self, testcase_empty_tree):
        tree, rendered, empty_arg = testcase_empty_tree
        print('', tree.render(empty=empty_arg), sep='\n')
        assert tree.render(empty=empty_arg) == rendered

    def test_render_invalid_style(self, testcase_simple_tree):
        tree, rendered, style = testcase_simple_tree
        with raises(ValueError, match=r"invalid style: expected \[.*\], got 'wrong'"):
            tree.render('wrong')

    @mark.parametrize('children_handle', ['invalid'], indirect=True)
    def test_invalid_children_handle(self, name_handle, children_handle, root_item):
        err_msg = r"children handle returned invalid result: expected List\[Item\], got 0"
        with raises(RuntimeError, match=err_msg):
            Tree.convert(root_item, name_handle, children_handle)

    def test_build_exceptions(self, testcase_exception_tree_items):
        items, rendered = testcase_exception_tree_items
        tree = Tree.build(items=items, naming='__name__', parent='__base__')
        print('', tree, sep='\n')
        assert tree.render() == rendered

    def test_build(self, testcase_tree_items):
        items, rendered = testcase_tree_items
        tree = Tree.build(items, 'name', 'parent')
        print('', tree, sep='\n')
        assert tree.render() == rendered

    def test_build_empty(self, testcase_empty_tree_items):
        items, rendered = testcase_empty_tree_items
        tree = Tree.build(items, 'name', 'parent')
        print('', tree.render(empty=rendered), sep='\n')
        assert tree.render(empty=rendered) == rendered

    def test_build_single_item(self, testcase_single_item_tree_items):
        items, rendered = testcase_single_item_tree_items
        tree = Tree.build(items, 'name', 'parent')
        print('', tree, sep='\n')
        assert tree.render() == rendered

    def test_build_star_layout(self, testcase_star_layout_tree_items):
        items, rendered = testcase_star_layout_tree_items
        tree = Tree.build(items, 'name', 'parent')
        print('', tree, sep='\n')
        assert tree.render() == rendered

    def test_build_chain_layout(self, testcase_chain_layout_tree_items):
        items, rendered = testcase_chain_layout_tree_items
        tree = Tree.build(items, 'name', 'parent')
        print('', tree, sep='\n')
        assert tree.render() == rendered

    @mark.parametrize('items_order', ['normal'], indirect=True)
    def test_build_missing_non_leaves_items(self, testcase_missing_tree_items, items_order):
        items, rendered = testcase_missing_tree_items
        tree = Tree.build(items, 'name', 'parent')
        print('', tree, sep='\n')
        assert tree.render() == rendered

    def test_build_multiple_roots(self, testcase_multiple_roots_tree_items):
        items = testcase_multiple_roots_tree_items
        with raises(RuntimeError, match='Given collection of items is not a connected graph!'):
            Tree.build(items, 'name', 'parent')

    @mark.xfail(reason='cycle references handling is not implemented')
    def test_build_cycle_references(self, testcase_cycle_references_tree_items):
        items = testcase_cycle_references_tree_items
        tree = Tree.build(items, 'name', 'parent')
        print('', tree, sep='\n')
        with raises(RecursionError):
            tree.render()


class TestAttrEnum:
    """
    Structure of dicts returned by most testcase fixtures:
        enum: AttrEnum = enum class under the test
        fields: list   = list of all field names declared in __fields__
        members: list  = list of all enum members
        string: str    = str(last_enum_member)
        representation: str = repr(last_enum_member)
        contents: list = contents of dir(last_enum_member)
        index          = last_enum_member.index
        value          = last_enum_member.value
        attrs: dict    = mapping of all declared field names
                         on their corresponding values of last_enum_member.
    """

    common_enum_dunders = ['__class__', '__doc__', '__fields__', '__module__']

    @staticmethod
    def gen_ids(lazy_fixture):
        return lazy_fixture.name.replace('testcase_enum_', '', 1)

# ————————————————————————————————————————————————————— Fixtures ————————————————————————————————————————————————————— #

    @fixture(scope='class')
    def testcase_doc_sample(self):
        class Sample(AttrEnum):
            __fields__ = 'attr1', 'attr2', 'attr3'
            A = 'data_A', 10, True
            B = 'data_B', 42
            C = 'data_C', 77
        return Sample

    @fixture(scope='class')
    def testcase_doc_value_sample(self):
        class ValueSample(AttrEnum):
            __fields__ = 'index', 'value'
            A = 1, 'data_A'
            B = 3, 'data_B'
            C = 2, 'data_C'
        return ValueSample

    @fixture(scope='class')
    def testcase_doc_void_sample(self):
        class VoidSample(AttrEnum):
            A = 2
            B = 7
            C = 9
        return VoidSample

    @fixture(scope='class')
    def testcase_enum_0f(self):
        class Enum0(AttrEnum):
            A = 'A_attr'
            B = 'B_attr'
            C = 'C_attr'

        return dict(
                enum     = Enum0,
                fields   = [],
                members  = [Enum0.A, Enum0.B, Enum0.C],
                string   = 'Enum0.C',
                representation = "<Enum0.C: 'C_attr'>",
                contents = [*self.common_enum_dunders, 'index', 'name', 'value'],
                index    = 2,
                value    = 'C_attr',
                attrs    = {},
        )

    @fixture(scope='class')
    def testcase_enum_1f(self):
        class Enum1(AttrEnum):
            __fields__ = 'f1',
            A = 'A_attr_1'
            B = 'B_attr_1'
            C = 'C_attr_1'

        return dict(
                enum     = Enum1,
                fields   = ['f1'],
                members  = [Enum1.A, Enum1.B, Enum1.C],
                string   = 'Enum1.C',
                representation = "<Enum1.C: f1='C_attr_1'>",
                contents = [*self.common_enum_dunders, 'f1', 'index', 'name', 'value'],
                index    = 2,
                value    = 'C_attr_1',
                attrs    = {'f1': 'C_attr_1'},
        )

    @fixture(scope='class')
    def testcase_enum_2f(self):
        class Enum2(AttrEnum):
            __fields__ = 'f1', 'f2'
            A = 'A_attr_1', 'A_attr_2'
            B = 'B_attr_1', 'B_attr_2'
            C = 'C_attr_1', 'C_attr_2'

        return dict(
                enum     = Enum2,
                fields   = ['f1', 'f2'],
                members  = [Enum2.A, Enum2.B, Enum2.C],
                string   = 'Enum2.C',
                representation = "<Enum2.C: f1='C_attr_1', f2='C_attr_2'>",
                contents = [*self.common_enum_dunders, 'f1', 'f2', 'index', 'name', 'value'],
                index    = 2,
                value    = ('C_attr_1', 'C_attr_2'),
                attrs    = {'f1': 'C_attr_1', 'f2': 'C_attr_2'},
        )

    enum_testcases = ['testcase_enum_0f', 'testcase_enum_1f', 'testcase_enum_2f']

    @fixture(scope='class', params=(lazy_fixture(case) for case in enum_testcases), ids=gen_ids.__func__)
    def testcase_enum_1_member(self, request):
        case = request.param

        class SingleEnum(AttrEnum):
            __fields__ = tuple(case['fields'])
            C = case['enum'].C.value

        return dict(
                enum     = SingleEnum,
                fields   = case['fields'],
                members  = [SingleEnum.C],
                string   = 'SingleEnum.C',
                representation = case['representation'].replace(case['string'], 'SingleEnum.C'),
                contents = case['contents'],
                index    = 0,
                value    = case['value'],
                attrs    = case['attrs'],
        )

    @fixture(scope='class')
    def testcase_enum_deficient_attrs(self):

        class DeficientEnum(AttrEnum):
            __fields__ = 'f1', 'f2'
            A = None
            B = ...
            C = 'C_attr_1'

        return dict(
                enum     = DeficientEnum,
                fields   = ['f1', 'f2'],
                members  = [DeficientEnum.A, DeficientEnum.B, DeficientEnum.C],
                string   = 'DeficientEnum.C',
                representation = "<DeficientEnum.C: f1='C_attr_1', f2=None>",
                contents = [*self.common_enum_dunders, 'f1', 'f2', 'index', 'name', 'value'],
                index    = 2,
                value    = ('C_attr_1', None),
                attrs    = {'f1': 'C_attr_1', 'f2': None},
        )

    @fixture(scope='class')
    def testcase_enum_value_ovr(self):
        class ValueEnum(AttrEnum):
            __fields__ = 'value',
            A = 'A_attr'
            C = 'C_attr'

        return dict(
                enum     = ValueEnum,
                fields   = ['value'],
                members  = [ValueEnum.A, ValueEnum.C],
                string   = 'ValueEnum.C',
                representation = "<ValueEnum.C: value='C_attr'>",
                contents = [*self.common_enum_dunders, 'index', 'name', 'value'],
                index    = 1,
                value    = 'C_attr',
                attrs    = {'value': 'C_attr'},
        )

    @fixture(scope='class')
    def testcase_enum_index_ovr(self):
        class IndexEnum(AttrEnum):
            __fields__ = 'index',
            A = 7
            C = 5

        return dict(
                enum     = IndexEnum,
                fields   = ['index'],
                members  = [IndexEnum.A, IndexEnum.C],
                string   = 'IndexEnum.C',
                representation = "<IndexEnum.C: index=5>",
                contents = [*self.common_enum_dunders, 'index', 'name', 'value'],
                index    = 5,
                value    = 5,
                attrs    = {'index': 5},
        )

    @fixture(scope='class')
    def testcase_enum_value_index_ovr(self):
        class ValueIndexEnum(AttrEnum):
            __fields__ = 'index', 'value'
            A = 7, 'A_attr'
            C = 5

        return dict(
                enum     = ValueIndexEnum,
                fields   = ['index', 'value'],
                members  = [ValueIndexEnum.A, ValueIndexEnum.C],
                string   = 'ValueIndexEnum.C',
                representation = "<ValueIndexEnum.C: index=5, value=None>",
                contents = [*self.common_enum_dunders, 'index', 'name', 'value'],
                index    = 5,
                value    = None,
                attrs    = {'index': 5, 'value': None},
        )

    @fixture(scope='class')
    def testcase_enum_empty(self):
        class EmptyEnum(AttrEnum):
            __fields__ = 'value', 'data'
        return EmptyEnum, ('value', 'data')

# ——————————————————————————————————————————————————————— Tests —————————————————————————————————————————————————————— #

    def test_doc(self, testcase_doc_sample):
        member = testcase_doc_sample.B
        assert member.name == 'B'
        assert member.index == 1
        assert member.value == ('data_B', 42, None)
        assert member.attr1 == 'data_B'
        assert member.attr2 == 42
        assert member.attr3 is None
        assert repr(member) == "<Sample.B: attr1='data_B', attr2=42, attr3=None>"

    def test_doc_value_enum(self, testcase_doc_value_sample):
        member = testcase_doc_value_sample.B
        assert member.name == 'B'
        assert member.index == 3
        assert member.value == 'data_B'
        assert repr(member) == "<ValueSample.B: index=3, value='data_B'>"

    def test_doc_void_enum(self, testcase_doc_void_sample):
        member = testcase_doc_void_sample.B
        assert member.name == 'B'
        assert member.index == 1
        assert member.value == 7
        assert repr(member) == "<VoidSample.B: 7>"

    all_enum_testcases = [
        *enum_testcases, 'testcase_enum_1_member', 'testcase_enum_deficient_attrs',
        'testcase_enum_value_ovr', 'testcase_enum_index_ovr', 'testcase_enum_value_index_ovr'
    ]

    @mark.parametrize('testcase', (lazy_fixture(case) for case in all_enum_testcases), ids=gen_ids.__func__)
    def test_enum(self, testcase):
        enum, fields, members, str_res, repr_res, dir_res, index, value, attrs = testcase.values()
        assert list(enum) == members
        assert str(enum.C) == str_res
        assert repr(enum.C) == repr_res
        assert dir(enum.C) == dir_res
        assert enum.C.index == index
        assert enum.C.value == value
        assert {attr: getattr(enum.C, attr) for attr in fields} == attrs
        assert enum['C'] == enum.C
        assert enum(value) == enum.C

    def test_enum_empty(self, testcase_enum_empty):
        enum, fields = testcase_enum_empty
        assert str(enum) == f"<enum '{enum.__name__}'>"
        assert list(enum) == []
        assert enum.__fields__ == fields
        with raises(KeyError):
            invalid = enum['__fields__']

    @mark.xfail(reason="enum should have at least one member - see AttrEnum 'Deny reserved names' comment")
    @mark.parametrize('name', ['name', '_sunder_', '__dunder__'])
    def test_invalid_field_no_members(self, name):
        with raises(ValueError):
            class InvalidFieldEnum(AttrEnum):
                __fields__ = 'valid', name, 'other'

    @mark.parametrize('name', ['name', '_sunder_', '__dunder__'])
    def test_invalid_field(self, name):
        with raises(ValueError, match=f"invalid field name '{name}'"):
            class InvalidFieldEnum(AttrEnum):
                __fields__ = 'valid', name, 'other'
                A = 'whatever'

    def test_too_many_attrs(self):
        class ValidEnum(AttrEnum):
            __fields__ = 'value', 'a', 'b'
            A = 1, 'A_a'
            B = 77, 'B_a', 'B_b'
        assert ValidEnum.A.value == 1
        assert ValidEnum.A.b is None
        assert ValidEnum.B.value == 77
        assert ValidEnum.B.b == 'B_b'

        with raises(ValueError, match="enum member has too many attrs: expected 3, got 4"):
            class TooManyAttrsEnum(AttrEnum):
                __fields__ = 'value', 'a', 'b'
                C = 42, 'C_a', 'C_b', 'extra'
