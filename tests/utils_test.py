from random import choices

from pytest import fixture, mark, raises

from utils import bytewise


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
        print(expected)
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
