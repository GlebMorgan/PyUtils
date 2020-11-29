from inspect import signature
from operator import itemgetter

from utils.bits import Bits
from pytest import mark, fixture, raises
from random import choice, randint


def check_result(method: str, operand, args, expected, *,
                 unpackargs: bool = False, subtype: type = False, kwargs: dict = None):
    if not kwargs:
        kwargs = {}
    if unpackargs is False:
        args = (args,)
    result = getattr(Bits(operand), method)(*args, **kwargs)
    assert result == expected
    assert type(result) is type(expected)
    if result and subtype:
        assert all(type(num) == subtype for num in result)


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

    @fixture(scope='class', params=patterns, ids=lambda par: ' '.join(par.split()))
    def data_set_bits(self, request):
        operand, args, result = request.param.strip().split()
        return int(operand, 2), tuple(int(n) for n in args), Bits(result, 2)

    @fixture(scope='class', params=map(invert_bits.__func__, patterns), ids=lambda par: ' '.join(par.split()))
    def data_clear_bits(self, request):
        operand, args, result = request.param.strip().split()
        return int(operand, 2), tuple(int(n) for n in args), Bits(result, 2)

    def test_set(self, data_set_bits):
        check_result('set', *data_set_bits, unpackargs=True)

    @mark.parametrize('bit', ('0', '123', None, 1.0))
    def test_set_invalid_bit(self, bit):
        with raises(TypeError):
            Bits(42).set(bit)

    def test_set_no_args(self):
        result = Bits(42).set()
        assert result == Bits(42)
        assert type(result) is Bits

    def test_clear(self, data_clear_bits):
        check_result('clear', *data_clear_bits, unpackargs=True)

    @mark.parametrize('bit', ('0', '123', None, 1.0))
    def test_clear_invalid_bit(self, bit):
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

    delimiters = '!@#$%^&*()_+?|/~abcXYZ. '

    @fixture(scope='class', params=patterns)
    def data_mask(self, request):
        operand, mask, result = request.param.strip().split()
        return int(operand, 2), mask, Bits(result, 2)

    @fixture(scope='class', params=patterns)
    def data_mask_delim(self, request):
        operand, mask, result = request.param.strip().split()
        if '-' in mask:
            mask = mask.replace('-', choice(self.delimiters))
        return int(operand, 2), mask, Bits(result, 2)

    def test_mask(self, data_mask):
        check_result('mask', *data_mask)

    def test_mask_delim(self, data_mask_delim):
        check_result('mask', *data_mask_delim)

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

    @fixture(scope='class', params=patterns, ids=lambda par: ' '.join(par.split()))
    def data_flag(self, request):
        operand, pos, result = request.param.strip().split()
        return int(operand, 2), int(pos), bool(int(result))

    def test_flag(self, data_flag):
        check_result('flag', *data_flag)


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

    @fixture(scope='class', params=patterns, ids=lambda par: ' '.join(par.split()))
    def data_flags(self, request):
        operand, n, result = request.param.strip().split()
        return int(operand, 2), int(n), tuple(bool(int(bit)) for bit in result[1:-1])

    def test_flags(self, data_flags):
        check_result('flags', *data_flags, subtype=bool)


class TestExtract:

    patterns = (
        ('00110101      1111  (101)       ', 'single num'),
        ('00110110    112233  (11 01 10)  ', 'multiple num'),
        ('00011001   111223-  (1 10 0)    ', 'delim'),
        ('00000010  11111111  (10)        ', 'single number'),
        ('11100011  --111     (11)        ', 'delim before'),
        ('11100011  111--     (0)         ', 'delim after'),
        ('10000011  11222333  (10 0 11)   ', 'no delims'),
        ('10000101  44423331  (1 0 10 100)', 'not in order'),
        ('00110101  -3331112  (10 1 11)   ', 'not in order + delim'),
        ('10000101  5555-001  (10 1 1000) ', 'missed markers'),
        ('11000001  11----22  (11 1)      ', 'long gap'),
        ('01100101  --112---  (10 0)      ', 'delim at the ends'),
        ('00000001  -------9  (1)         ', 'long delim'),
        ('01000100  -1-2-3-4  (1 0 1 0)   ', 'single bit nums'),
    )

    @fixture(params=patterns, ids=itemgetter(1))
    def data_extract(self, request, res_type):
        operand, mask, result = request.param[0].strip().split(maxsplit=2)
        return int(operand, 2), mask, res_type(int(num, 2) for num in result[1:-1].split())

    @fixture(params=patterns, ids=itemgetter(1))
    def data_extract_sep(self, request, method, res_type):
        operand, mask, result = request.param[0].strip().split(maxsplit=2)
        sep_count = randint(1, 5)
        sep = signature(getattr(Bits, method)).parameters['sep'].default
        markers = list(mask)
        for i in range(sep_count):
            markers.insert(randint(0, len(mask)), sep)
        return int(operand, 2), ''.join(markers), res_type(int(num, 2) for num in result[1:-1].split())

    @mark.parametrize('method, res_type', [('extract', tuple), ('extract2', list)])
    def test_extract(self, data_extract, method, res_type):
        check_result(method, *data_extract, subtype=int)

    @mark.parametrize('method, res_type', [('extract', tuple), ('extract2', list)])
    def test_extract_sep(self, data_extract_sep, method, res_type):
        check_result(method, *data_extract_sep, subtype=int)

    @mark.parametrize('method', ('extract', 'extract2'))
    def test_extract_duplicate_markers(self, method):
        extract = getattr(Bits(42), method)
        with raises(ValueError):
            extract('11-21')

    @mark.parametrize('method, res_type', [('extract', tuple), ('extract2', list)])
    def test_extract_empty(self, method, res_type):
        extract = getattr(Bits(42), method)
        assert extract('') == res_type()
        assert extract('---') == res_type()
        assert extract('@') == res_type()

    @mark.parametrize('sep', ('', ' ', '@', 'sep', False), ids='sep={}'.format)
    @mark.parametrize('method, res_type', [('extract', tuple), ('extract2', list)])
    def test_extract_custom_sep(self, method: str, res_type: type, sep: str):
        value = 0b00110101
        mask = '{sep}1333{sep}22--'.format(sep=sep if sep else '')
        expected = res_type((0, 1, 0b11))
        check_result(method, value, mask, expected, subtype=int, kwargs={'sep': sep})


class TestCompose:

    patterns = ('1101001', '1000000', '111', '000', '1', '0', '')

    @fixture(scope='class', params=patterns)
    def data_compose(self, request):
        pattern = request.param
        flags = tuple(bool(int(bit)) for bit in pattern) if pattern else ()
        result = Bits(''.join(reversed(pattern)), 2) if pattern else Bits()
        return 0, flags, Bits(result)

    def test_compose(self, data_compose):
        check_result('compose', *data_compose, unpackargs=True)

    def test_compose_int(self):
        check_result('compose', 0, (1, 1, 0, 1, 0, 0), Bits(0b1011), unpackargs=True)

    def test_compose_generator(self):
        def gen_flags():
            for flag in '110100':
                yield bool(int(flag))
        check_result('compose', 0, gen_flags(), Bits(0b1011), unpackargs=True)


class TestPack:

    patterns = (
        ('10011010  -00--1--  11 1       11111110', 'general case'),
        ('00001000  000       101        00001101', 'single'),
        ('00001000  000--     101        00010100', 'single + delim'),
        ('00001000  -000--    101        00010100', 'single + 2x delim'),
        ('00010001  0         0          00010000', 'single bit'),
        ('00110011  000-----  10         01010011', 'start'),
        ('11001100  ------00  11         11001111', 'end'),
        ('11100010  00-11--2  00 11 1    00111011', 'triple'),
        ('00000000  0------1  1 0        10000000', 'edges'),
        ('10101010  00011222  10 10 101  01010101', 'no gaps'),
        ('11110000  01222234  0 1 1 0 1  01000101', 'bits'),
        ('10011100  -00-1-00  11 0       11110111', 'dups'),
        ('10100010  00000000  11111111   11111111', 'whole range'),
        ('00000001  000--11-  1 11       00100111', 'expand to left'),
        ('00001111  0111-11-  1 101      11011011', 'different group lengths'),
        ('10100001  -         1 1011 0   10100001', 'empty'),
    )

    @fixture(scope='class', params=patterns, ids=itemgetter(1))
    def data_pack(self, request):
        operand, mask, *args, result = request.param[0].strip().split()
        return int(operand, 2), (mask, *(int(num, 2) for num in args)), Bits(result, 2)

    @fixture(scope='class')
    def data_pack_sep(self, data_pack):
        operand, args, result = data_pack
        mask, *args = args
        sep_count = randint(1, 5)
        sep = signature(Bits.pack).parameters['sep'].default
        markers = list(mask)
        for i in range(sep_count):
            markers.insert(randint(0, len(mask)), sep)
        return operand, (''.join(markers), *args), result

    def test_pack(self, data_pack):
        check_result('pack', *data_pack, unpackargs=True)

    def test_pack_sep(self, data_pack_sep):
        check_result('pack', *data_pack_sep, unpackargs=True)

    def test_pack_empty_nums(self):
        with raises(ValueError):
            Bits(42).pack('00--')

    def test_pack_empty_mask(self):
        assert Bits().pack('', 1, 2, 3) == Bits()

    def test_pack_empty_args(self):
        assert Bits(42).pack('') == Bits(42)
        assert Bits(42).pack('---') == Bits(42)
        assert Bits(42).pack('rubbish') == Bits(42)

    @mark.parametrize('sep', ('', ' ', '@', 'sep', False), ids='sep={}'.format)
    def test_pack_custom_sep(self, sep):
        value = 0b10
        mask = '{sep}0011{sep}22--'.format(sep=sep if sep else '')
        nums = (0b11, 0, 1)
        expected = Bits(0b1100_0110)
        check_result('pack', value, (mask, *nums), expected, unpackargs=True, kwargs={'sep': sep})

    @mark.parametrize('mask, args', (('00112200--3-', '1 2 10'), ('11--', '0')), ids=itemgetter(0))
    def test_pack_invalid(self, mask, args):
        with raises(ValueError):
            Bits(42).pack(mask, *(int(num) for num in args))
