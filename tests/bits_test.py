from utils import Bits
from pytest import mark, fixture, raises


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
