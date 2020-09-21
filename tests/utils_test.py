from inspect import signature
from operator import itemgetter
from random import choices

from pytest import fixture, mark, raises, warns

from utils import bytewise, bitwise, deprecated


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
