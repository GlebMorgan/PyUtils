from pytest import fixture


fixture_params = ((1, 0), (2, 5))


@fixture(params=fixture_params, ids=lambda par: f"{par[0]} and {par[1]}")
def fixture_parametrized(request):
    print('\n<fixture startup>')
    print(f'Request object: {request}')
    print(f'Request attrs:')
    print(*(f'    {attr} = {getattr(request, attr)}' for attr in request.__dict__), sep='\n')
    yield request.param
    print('\n<fixture teardown>')


def test_fixture_parametrize(fixture_parametrized):
    arg = fixture_parametrized
    assert isinstance(arg, tuple)


# ———————————————————————————————————————————————————————————————————————————————————————————————————————————————————— #


fixture_nested_params = (1, 7)


@fixture(params=fixture_nested_params)
def fixture_nested(request, fixture_parametrized):
    yield sum(fixture_parametrized), request.param


def test_fixture_nested(fixture_nested):
    arg = fixture_nested
    assert arg[0] == arg[1]
