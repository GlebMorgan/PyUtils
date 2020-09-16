from pytest import fixture, mark


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


# ——————————————————————————— Fixture parametrization via @mark.parametrize(indirect=True) ——————————————————————————— #

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


# ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————— #
