from utils import Bits
from pytest import mark, fixture, raises
from random import choice


@mark.skip(reason='methods signature change')
class TestSet:

    patterns_single_bit = (
        '1110 0 1111',
        '1111 0 1111',
        '1101 1 1111',
        '1100 1 1110',
        '0000 0 0001',
        '0001 0 0001',
        '0000 1 0010',
        '0010 1 0010',
        '1011 2 1111',
        '0100 2 0100'
    )

    patterns_multiple_bit = (
        '0000 01  0011',
        '0011 01  0011',
        '0000 123 1110',
        '0110 123 1110',
        '0100 123 1110',
        '0000 000 0001',
        '0001 000 0001',
        '0000 32  1100',
        '1111 32  1111',
        '0000 010 0011',
        '0010 101 0011',
        '0111 100 0111',
        '0100 001 0111',
    )

    patterns_all = patterns_single_bit + patterns_multiple_bit

    @staticmethod
    def pattern_invert_bits(pattern_list):
        new_pattern_list = []
        for pat in pattern_list:
            operand, bits, result = pat.split()
            operand = operand.replace('1', '-').replace('0', '1').replace('-', '0')
            result = result.replace('1', '-').replace('0', '1').replace('-', '0')
            new_pattern_list.append(' '.join((operand, bits, result)))
        return new_pattern_list

    @staticmethod
    def ids_tuple(pattern):
        num, bits, _ = pattern.split()
        return f'''{num}-({bits})'''

    @staticmethod
    def ids_list(pattern):
        num, bits, _ = pattern.split()
        return f'''{num}-[{bits}]'''

    @staticmethod
    def ids_single(pattern):
        return '-'.join(pattern.split()[:2])

    @fixture(params=patterns_single_bit, ids=ids_single.__func__)
    def data_set_single_bit(self, request):
        operand, args, result = request.param.split()
        yield int(operand, 2), int(args[0]), int(result, 2)

    @fixture(params=patterns_all, ids=ids_tuple.__func__)
    def data_set_tuple(self, request):
        operand, args, result = request.param.split()
        yield int(operand, 2), tuple(int(n) for n in args), int(result, 2)

    @fixture(params=patterns_all, ids=ids_list.__func__)
    def data_set_list(self, request):
        operand, args, result = request.param.split()
        yield int(operand, 2), list(int(n) for n in args), int(result, 2)

    @fixture(params=pattern_invert_bits.__func__(patterns_single_bit), ids=ids_single.__func__)
    def data_clear_single_bit(self, request):
        operand, args, result = request.param.split()
        yield int(operand, 2), int(args[0]), int(result, 2)

    @fixture(params=pattern_invert_bits.__func__(patterns_all), ids=ids_tuple.__func__)
    def data_clear_tuple(self, request):
        operand, args, result = request.param.split()
        yield int(operand, 2), tuple(int(n) for n in args), int(result, 2)

    @fixture(params=pattern_invert_bits.__func__(patterns_all), ids=ids_list.__func__)
    def data_clear_list(self, request):
        operand, args, result = request.param.split()
        yield int(operand, 2), list(int(n) for n in args), int(result, 2)

    def test_set_single_bit(self, data_set_single_bit):
        operand, bit, expected = data_set_single_bit
        result = Bits(operand).set(bit)
        assert result == expected

    def test_set_tuple_bit(self, data_set_tuple):
        operand, bit, expected = data_set_tuple
        result = Bits(operand).set(bit)
        assert result == expected

    def test_set_list_bit(self, data_set_list):
        operand, bit, expected = data_set_list
        result = Bits(operand).set(bit)
        assert result == expected

    @mark.parametrize('bit', ('0', '123', None, 1.0))
    def test_set_invalid_bit(self, bit):
        with raises(TypeError):
            Bits(42).set(bit)

    def test_clear_single_bit(self, data_clear_single_bit):
        operand, bit, expected = data_clear_single_bit
        result = Bits(operand).clear(bit)
        assert result == expected

    def test_clear_tuple_bit(self, data_clear_tuple):
        operand, bit, expected = data_clear_tuple
        result = Bits(operand).clear(bit)
        assert result == expected

    def test_clear_list_bit(self, data_clear_list):
        operand, bit, expected = data_clear_list
        result = Bits(operand).clear(bit)
        assert result == expected

    @mark.parametrize('bit', ('0', '123', None, 1.0))
    def test_clear_invalid_bit(self, bit):
        with raises(TypeError):
            Bits(42).set(bit)


class TestSetClear:

    patterns = (
        '1110 0   1111',
        '1111 0   1111',
        '1101 1   1111',
        '1100 1   1110',
        '0000 0   0001',
        '0001 0   0001',
        '0000 1   0010',
        '0010 1   0010',
        '1011 2   1111',
        '0100 2   0100',
        '0000 01  0011',
        '0011 01  0011',
        '0000 123 1110',
        '0110 123 1110',
        '0100 123 1110',
        '0000 000 0001',
        '0001 000 0001',
        '0000 32  1100',
        '1111 32  1111',
        '0000 010 0011',
        '0010 101 0011',
        '0111 100 0111',
        '0100 001 0111',
    )

    @staticmethod
    def invert_bits(pattern):
        operand, bits, result = pattern.split()
        operand = operand.replace('1', '-').replace('0', '1').replace('-', '0')
        result = result.replace('1', '-').replace('0', '1').replace('-', '0')
        return ' '.join((operand, bits, result))

    @fixture(params=patterns, ids=lambda par: ' '.join(par.split()))
    def data_set_bits(self, request):
        operand, args, result = request.param.split()
        yield int(operand, 2), *tuple(int(n) for n in args), int(result, 2)

    @fixture(params=map(invert_bits.__func__, patterns), ids=lambda par: '-'.join(par.split()))
    def data_clear_bits(self, request):
        operand, args, result = request.param.split()
        yield int(operand, 2), *tuple(int(n) for n in args), int(result, 2)

    def test_set_bits(self, data_set_bits):
        operand, *bits, expected = data_set_bits
        result = Bits(operand).set(*bits)
        assert result == expected
        assert type(result) is Bits

    @mark.parametrize('bit', ('0', '123', None, 1.0))
    def test_set_invalid_bit(self, bit):
        with raises(TypeError):
            Bits(42).set(bit)

    def test_set_no_args(self):
        result = Bits(42).set()
        assert result == Bits(42)
        assert type(result) is Bits

    def test_clear_bits(self, data_clear_bits):
        operand, *bits, expected = data_clear_bits
        result = Bits(operand).clear(*bits)
        assert result == expected
        assert type(result) is Bits

    @mark.parametrize('bit', ('0', '123', None, 1.0))
    def test_set_invalid_bit(self, bit):
        with raises(TypeError):
            Bits(42).clear(bit)

    def test_clear_no_args(self):
        result = Bits(42).clear()
        assert result == Bits(42)
        assert type(result) is Bits


class TestMask:

    patterns = (
        '0000 ---- 0000',
        '1111 -    1111',
        '1110 ---1 1111',
        '1111   -1 1111',
        '1110    1 1111',
        '0011 --00 0000',
        '0000 --00 0000',
        '1010 0--1 0011',
        '0000 -1   0001',
        '0000 1-   0010',
        '0000 0000 0000',
        '1111 0000 0000',
        '0000 1111 1111',
        '0000 -1-1 0101',
        '1111 -0-1 1011',
        '0001 1--- 1001',
        '1001 1--- 1001',
    )

    random_marker_patterns = tuple(
            pattern.replace('-', choice('!@#$%^&*()_+?|/~123abcXYZ.'))
            for pattern in patterns if '-' in pattern
    )
    patterns_all = patterns + random_marker_patterns

    @fixture(params=patterns_all, ids=lambda par: ' '.join(par.split()))
    def data_mask(self, request):
        operand, mask, result = request.param.split()
        yield int(operand, 2), mask, int(result, 2)

    def test_mask(self, data_mask):
        operand, mask, expected = data_mask
        result = Bits(operand).mask(mask)
        assert result == expected
        assert type(result) is Bits

    @mark.parametrize('mask', (0, Bits, None, 1.0))
    def test_mask_invalid(self, mask):
        with raises(TypeError):
            Bits(42).mask(mask)

    def test_mask_empty(self):
        result = Bits(42).mask('')
        assert result == Bits(42)
        assert type(result) is Bits


class TestFlag:

    patterns = (
     '   0 0 0',
     '   0 3 0',
     '   1 0 1',
     '   1 3 0',
     '0110 1 1',
     '0100 1 0',
    )

    @fixture(params=patterns, ids=lambda par: ' '.join(par.split()))
    def data_flag(self, request):
        operand, pos, result = request.param.strip().split()
        yield int(operand, 2), int(pos), bool(int(result))

    def test_flag(self, data_flag):
        operand, pos, expected = data_flag
        result = Bits(operand).flag(pos)
        assert result == expected
        assert type(result) is bool


class TestFlags:

    patterns = (
        '0000 0 ()',
        '0001 0 ()',
        '0000 1 (0)',
        '0001 1 (1)',
        '1111 4 (1111)',
        '0001 4 (1000)',
        '0110 2 (01)',
    )

    @fixture(params=patterns, ids=lambda par: ' '.join(par.split()))
    def data_flags(self, request):
        operand, n, result = request.param.split()
        yield int(operand, 2), int(n), tuple(bool(int(bit)) for bit in result[1:-1])

    def test_flags(self, data_flags):
        operand, n, expected = data_flags
        result = Bits(operand).flags(n)
        assert result == expected
        assert type(result) is tuple
        assert type(result[0]) is bool if len(result) != 0 else result == ()
