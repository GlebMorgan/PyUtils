from pytest import fixture, mark, lazy_fixture


# ————————————————————————————————— Fixture parametrization via @fixture(params=...) ————————————————————————————————— #

fixture_params = ((1, 0), (2, 5))


@fixture(params=fixture_params, ids=lambda par: f"{par[0]} and {par[1]}")
def fixture_with_params(request):
    print('\n<fixture startup>')
    print(f'Request object: {request}')
    print(f'Request attrs:')
    print(*(f'    {attr} = {getattr(request, attr)}' for attr in request.__dict__), sep='\n')
    yield request.param
    print('\n<fixture teardown>')


def test_fixture_parametrize(fixture_with_params):
    arg = fixture_with_params
    assert isinstance(arg, tuple)


# ————————————————————————————————————————————————— Nested fixtures —————————————————————————————————————————————————— #

fixture_nested_params = (1, 7)


@fixture(params=fixture_nested_params)
def fixture_nested(request, fixture_with_params):
    yield sum(fixture_with_params), request.param


def test_fixture_nested(fixture_nested):
    arg = fixture_nested
    assert 1


# ———————————————————————————— Parametrization of fixture arguments via @mark.parametrize ———————————————————————————— #

@fixture(params=('a', 'b', 'c', 'd', 'e'))
def fixture_parametrize(request, arg):
    print()
    print(f'{arg=}, {request.param=}')
    yield arg+1


@mark.parametrize('arg', (1, 2, 3, 4, 5))
def test_fixture_parametrize(fixture_parametrize, arg):
    assert type(fixture_parametrize) is int


# —————————————————————————————————————————————————— Request.module —————————————————————————————————————————————————— #

@fixture(scope='module')
def fixture_scope_module(request):
    print(f'Request object: {request}')
    print(f'Request attrs:')
    print(*(f'    {attr} = {getattr(request, attr)}' for attr in request.__dict__), sep='\n')
    print(f'Request.module: {request.module}')
    print(f'Request.module attrs: {dir(request.module)}')
    yield 1


def test_fixture_scope_module(fixture_scope_module):
    arg = fixture_scope_module
    assert arg == 1


# ——————————————————— Multi-level fixture parametrization via combining inside aggregator fixture ———————————————————— #

@fixture(params=(1, 2, 3))
def fixture_nums(request):
    return request.param


@fixture(params=('a', 'b', 'c'))
def fixture_chars(request):
    return request.param


@fixture(params=(True, False))
def fixture_combine(request, fixture_nums, fixture_chars):
    return str(fixture_nums) + fixture_chars + str(request.param)


def test_combined_fixture(fixture_combine):
    print(fixture_combine)


# ————————————————————————————————————————————— Lazy fixtures (plugin) ——————————————————————————————————————————————— #

def func1():
    return 42


def func2():
    return 's'


for f in [func1, func2]:
    name = 'fixture'+f.__name__[-1]
    globals()[name] = fixture(scope='function', name=name)(f)


@mark.parametrize('fix', (lazy_fixture('fixture1'), lazy_fixture('fixture2')))
def test_dynamic_fixture(fix):
    print(fix)


# ————————————————————————————————————————————— Dict fixture params (fail) ——————————————————————————————————————————— #

d = dict(a=3, b=5, c=0)


@fixture(params=d.values(), ids=d.keys())
def fixture_dict_params(request):
    return request.param


def test_fixture_dict_params(fixture_dict_params):
    print(fixture_dict_params)


# ——————————————————————————————————————————— @fixture(ids=...) techniques ——————————————————————————————————————————— #

@fixture(params=((1, 'a'), (2, 'b'), (3, 'c')), ids='{[1]}-test'.format)
def fixture_ids_using_format(request):
    return request.param


def test_fixture_ids_using_format(fixture_ids_using_format):
    print(fixture_ids_using_format)


# ———————————————————————————————————————— Implicit indirect parametrization ————————————————————————————————————————— #

@fixture(params=[1, 2, 3], ids='param={}'.format)
def fixture_indirect_parameter(request, par):
    return request.param, par


@mark.parametrize('par', ['ok'])
def test_fixture_indirect_parameter(fixture_indirect_parameter, par):
    print(fixture_indirect_parameter, par)
