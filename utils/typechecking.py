"""
Module for annotation-driven function call typechecking with no inspection of content for container objects
Ideologically intended for human-bound use cases such as rough user input viability checks

API:
    • @check_args – decorator that performs typechecking on specified (or all) arguments
        of the decorated function / method immediately before the actual call

Typecheck machinery glossary:
    • type annotation (annotation) - entire annotation expression:
        `Dict[str, Union[List[int], int]]`, etc.
    • type specificator (typespec) - any structural component of type annotation:
        `Iterable[int]`, `Tuple`, `Union[int, Collection[int]]`, `Any`, `type`, etc.
    • type origin (basetype) – upper component of some given subscriptable typespec:
        `Union`, `List`, `int`, `TypeVar`, etc.
    • type arguments (typeargs) - set of arguments of some given subscriptable typespec:
        `[str, Dict[str, int]]`, `[]`, `[Optional[Callable]]`, `[bool, ...]`, etc.

Supported features:
    • first-level typechecking against provided type annotation
    • all type specificators provided by `typing` module for Python 3.8
    • structure checks for `Tuple`, excluding homogeneous tuples (like `Tuple[str, ...]`)
    • structure checks for `TypedDict`
    • subclass checks for `NamedTuple`
    • typechecking against bound types and constraints of `TypeVar`s
    • runtime-checkable `Protocol`s
    • simplified `IO` class checks
    • automatic `None` -> `NoneType` conversion (by `typing.get_type_hints()` used under the hood)

Behaviours that this module was NOT designed to support:
    • inspecting of contents for iterables and containers, including homogeneous tuple typespecs
    • inspecting callable signatures
    • inspecting annotations of interface and protocol classes
    • checks that involve applying a specific type to generic classes
    • rigorous subclass checks of complex type specificators inside `Type[...]`
    • complicated `IO` type checks
    • resolving sForwardRef`s

Supported type specifications:
    • Bare types, including NoneType
    • SpecialForms:
        Any, ClassVar, Final, Literal, Optional, Union
    • Interfaces:
        Awaitable, Callable, ContextManager, AsyncContextManager, Coroutine, Generator,
        AsyncGenerator, Hashable, Iterable, AsyncIterable, Iterator, AsyncIterator, Reversible, Sized
    • Protocols:
        SupportsAbs, SupportsBytes, SupportsComplex, SupportsFloat, SupportsIndex, SupportsInt, SupportsRound
    • Custom runtime-checkable protocols (derived from Protocol)
    • Containers:
        ChainMap, Collection, Container, Counter, Deque, Dict, DefaultDict, OrderedDict,
        ItemsView, KeysView, ValuesView, List, Mapping, MutableMapping, MappingView, Sequence, MutableSequence,
        Set, FrozenSet, AbstractSet, MutableSet, Tuple
    • Type references:
        Type, ByteString, Pattern, Match, IO, TextIO, BinaryIO
    • Generic classes
    • TypedDict classes
    • NamedTuple classes
    • TypeVars
"""

from inspect import signature
from io import IOBase, TextIOBase, BufferedIOBase
from typing import *
from typing import IO, TextIO, BinaryIO, Match, Pattern
from typing import _GenericAlias as GenericAlias
from typing import _SpecialForm as SpecialForm
from typing import _TypedDictMeta as TypedDictMeta

from wrapt import decorator


# TODO: support subscripted builtins and ABCs like `list[str]` in Python 3.9


NoneType = type(None)
Typespec = Union[type, SpecialForm, GenericAlias, TypeVar]

IO_type_refs = {
    IO: IOBase,
    TextIO: TextIOBase,
    BinaryIO: BufferedIOBase,
}


def _format_type_(typevar: Typespec) -> str:
    """
    Return string representation of a given typespec
    Removes 'typing.' prefix for objects from `typing` module
    """

    if isinstance(typevar, type):
        return typevar.__name__
    else:
        return str(typevar).replace('typing.', '')


class TypecheckError(Exception):
    """Runtime type checking failed"""

    def __init__(self, template: str = None, *, value: Any, exptype: Typespec, varname: str):
        self.value = value
        self.typespec = exptype
        if not template:
            template = "{value!r:.100} is not {exptype}"
        message = template.format(value=value, exptype=_format_type_(exptype), varname=varname)
        super().__init__(f"argument '{varname}': " + message)


def check_args(arguments: Union[None, str, Iterable[str]]):
    """
    Decorator for typechecking wrapped function / method parameters as specified in 'arguments'
    Checks are performed against argument annotations of wrapped callable at the time it is being called
    Argument names may be specified as either a string with comma-separated names or just as a list of names.
    If `arguments` are omitted, typeckecking is performed on all the parameters being passed to wrapped callable
    If wrapped function / method is already decorated, `@check_args` should be applied beforehand in most cases
    If some argument of wrapped callable has default value set to `None`, its annotation is
        automatically converted to `Optional[<annotation>]` (by `typing.get_type_hints()` used under the hood)
    >>> @check_args
    >>> def func(a: Union[int, Dict[str, int], Tuple[Any, str]]):
    >>>     ...
    >>> func(1)  # typechecks: `1` is an `int`
    >>> func(True)  # typechecks: `bool` is a subclass of `int`
    >>> func({})  # typechecks: empty dict is a `dict`
    >>> func({1: True, 2: 's'})  # typechecks: dict contents are not inspected
    >>> func((object, 's'))  #typechecks: argument is a `tuple` and its structure matches annotation signature
    >>> func(None)  # fails: `NoneType` does not match any one of given specifications
    >>> func(('s', 0))  # fails: the second item of the tuple does not match given `str` specification
    >>> func((0, 's', 'extra'))  # fails: tuple has an extra element

    >>> @check_args('a, b')
    >>> def func(a: Any, b: int, c: bool):
    >>>     ...
    >>> func(object, 1, 's')  # typechecks: only 'a' and 'b' arguments are checked
    """

    def function_processor(function):
        nonlocal argnames
        type_hints = get_type_hints(function)
        sign = signature(function)

        # Get annotations mapping for requested arguments
        if not argnames:
            annotations = type_hints
            annotations.pop('return', None)
        else:
            if isinstance(argnames, str):
                argnames = filter(None, (arg.strip() for arg in argnames.split(',')))
            annotations = {}
            names = tuple(sign.parameters.keys())
            for name in argnames:
                if name not in names:
                    raise ValueError(f"non-existent argument name '{name}'"
                                     f" for function '{function.__name__}'")
                annotations[name] = type_hints[name]

        @decorator
        def wrapper(func, instance, args, kwargs):
            parameters = sign.bind(*args, **kwargs)
            parameters.apply_defaults()
            for argname, annotation in annotations.items():
                _check_type_(parameters.arguments[argname], annotation, argname=argname)
            return func(*args, **kwargs)

        return wrapper(function)

    if isinstance(arguments, (str, Iterable)) or arguments is None:
        # Infer decorator is used with an argument, thus `arguments` contains argument names to be checked
        argnames = arguments
        return function_processor
    else:
        # Infer decorator is used without arguments, thus `arguments` is a callable to be wrapped
        argnames = None
        return function_processor(arguments)


def _check_type_(value: Any, typespec: Typespec, *, argname: str):
    """
    Typecheck `value` against `typespec`
    Raises `TypecheckError` on fail, otherwise returns `None`
    Valid types for `typespec`: pure `type`, `GenericAlias`, `SpecialForm`, `TypeVar`, `TypedDict`, `NamedTuple`
    Valid argument types for generic `Type[...]: pure `type`, `Any`, `GenericAlias`, `NamedTuple`
    `ForwardRef`s anywhere inside typespec are not supported, annotations should be resolved prematurely
    Subscripted `IO`s, `NoReturn`s and `TypedDict` class checks are not supported
    See module docstring for full list of supported type specifications
    """

    # Fast-forward most basic types
    if typespec in (str, int, float, bool, bytes, type, dict, tuple, list, set, NoneType):
        if isinstance(value, typespec):
            return
        raise TypecheckError(value=value, exptype=typespec, varname=argname)

    # Fast-forward `Any`
    if typespec is Any:
        return

    if isinstance(typespec, type):
        # `NamedTuple` itself is not a base type for NamedTuples, so it is not directly typecheckable,
        #   but it adds `_fields` and `_field_defaults` attributes which give a chance to guess
        if typespec is NamedTuple:
            if value.__class__.__bases__ == (tuple,):
                if hasattr(value, '_fields') and hasattr(value, '_field_defaults'):
                    return  # infer that's a NamedTuple
            raise TypecheckError(value=value, exptype=typespec, varname=argname)

        # `TypedDict` subclasses have `__annotations__` and `__total__` that allow for typechecking
        if type(typespec) is TypedDictMeta:
            typespec: TypedDictMeta

            if typespec is TypedDict:
                raise TypeError(f"argument '{argname}': bare TypedDict does not support typechecking")

            # Check base type to be a `dict`
            if not isinstance(value, dict):
                raise TypecheckError(value=value, exptype=dict, varname=argname)

            annotations = get_type_hints(typespec)

            # Check value has the same set of keys as specified in typespec
            if typespec.__total__ is True:
                if (actual_keys := set(value.keys())) != (expected_keys := set(annotations.keys())):
                    message = "{exptype} layout mismatch: " \
                              f"expected ({', '.join(expected_keys)}), got ({', '.join(actual_keys)})"
                    raise TypecheckError(message, value=value, exptype=typespec, varname=argname)
            else:
                if not (actual_keys := set(value.keys())).issubset(expected_keys := set(annotations.keys())):
                    message = "{exptype} layout mismatch: " \
                              f"extra keys: ({', '.join((actual_keys - expected_keys))})"
                    raise TypecheckError(message, value=value, exptype=typespec, varname=argname)

            # Check type of each item in the dictionary
            for key, item in value.items():
                annotation = annotations[key]
                try:
                    _check_type_(item, annotation, argname=argname)
                except TypecheckError:
                    message = f"{_format_type_(typespec)} layout mismatch: key '{key}' =" \
                              " {value!r:.50} is not {exptype}"
                    raise TypecheckError(message, value=item, exptype=annotation, varname=argname) from None

            # Return without error if all types have matched
            return

        # `IO` types are not actually base types for file objects, so they require special handling
        if issubclass(typespec, IO):
            # CONSIDER: find better approach for checking IO and Type[IO]
            if isinstance(value, IO_type_refs.get(typespec, object)):
                return
            raise TypecheckError(value=value, exptype=typespec, varname=argname)

        # All other `type`s are treated the usual way
        if isinstance(value, typespec):
            return
        raise TypecheckError(value=value, exptype=typespec, varname=argname)

    # `TypeVar` instances provide `__bound__` and `__constraints__` to check against
    if isinstance(typespec, TypeVar):
        typespec: TypeVar

        if typespec.__constraints__:
            for constraint in typespec.__constraints__:
                try:
                    _check_type_(value, constraint, argname=argname)
                except TypecheckError:
                    continue
                else:
                    return
            message = "{value!r:.100} does not match any constraint from" \
                      f" [{', '.join(map(_format_type_, typespec.__constraints__))}]"
            raise TypecheckError(message, value=value, exptype=typespec, varname=argname)

        if typespec.__bound__ is not None:
            return _check_type_(value, typespec.__bound__, argname=argname)

        return  # not constrained => accepts any type

    # Extract base type and type arguments from subscripted `GenericAlias`es like `Dict[int, str]`
    if isinstance(typespec, GenericAlias) and typespec._special is False:
        basetype = typespec.__origin__
        typeargs = typespec.__args__
    else:
        basetype = typespec
        typeargs = None

    # `SpecialForm`s like `Union` have special handling:
    if isinstance(basetype, SpecialForm):
        # Bare `SpecialForm`s serve no purpose
        if not typeargs:
            raise TypeError(f"argument '{argname}': bare {basetype._name} is invalid type specification")

        if basetype is ClassVar or basetype is Final:
            return _check_type_(value, typeargs[0], argname=argname)

        if basetype is Literal:
            if value in typeargs:
                return
            message = "{value!r:.100} does not match any value from {exptype}"
            raise TypecheckError(message, value=value, exptype=typespec, varname=argname)

        if basetype is Union:
            for typearg in typeargs:
                try:
                    _check_type_(value, typearg, argname=argname)
                except TypecheckError:
                    continue
                else:
                    return
            message = "{value!r:.100} does not match any type specification from {exptype}"
            raise TypecheckError(message, value=value, exptype=typespec, varname=argname)

    # All other typespecs gonna have their basetype typechecked the usual way
    try:
        if not isinstance(value, basetype):
            raise TypecheckError(value=value, exptype=basetype, varname=argname)
    except TypeError:
        if isinstance(typespec, ForwardRef):
            # Explicitly deny `ForwardRef`s
            message = "ForwardRefs are not allowed. All annotations are expected to be resolved"
            raise TypeError(f"argument '{argname}': " + message)
        else:
            # Show more relevant error message otherwise
            message = f"{typespec} is not a valid type specification"
            raise TypeError(f"argument '{argname}': " + message) from None

    # Check type arguments, if provided
    if typeargs:
        # `Tuple` arguments define fixed structure, if not specified as homogeneous collection
        if typespec._name == 'Tuple':
            value: tuple

            if len(typeargs) > 1 and typeargs[-1] is Ellipsis:
                return  # dont inspect contents of collections of homogeneous type

            if len(value) != len(typeargs):
                message = f"tuple signature mismatch: required {len(typeargs)} arguments, got {len(value)}"
                raise TypecheckError(message, value=value, exptype=typespec, varname=argname)

            for i, (item, typearg) in enumerate(zip(value, typeargs), start=1):
                try:
                    _check_type_(item, typearg, argname=argname)
                except TypecheckError:
                    message = f"tuple signature mismatch: item #{i} =" " {value!r:.100} is not {exptype}"
                    raise TypecheckError(message, value=item, exptype=typearg, varname=argname) from None

            return  # return without error if all types have matched

        # `Type` argument defines type(s) for subclass check
        if typespec._name == 'Type':
            typearg = typeargs[0]

            if typearg is Any:
                return

            if typearg is NamedTuple:
                if value.__bases__ == (tuple,) and hasattr(value, '_fields') and hasattr(value, '_field_defaults'):
                    return

            if isinstance(typearg, GenericAlias):
                typearg = typearg.__origin__

            if not isinstance(typearg, type):
                raise TypeError(f"argument '{argname}': type argument '{_format_type_(typearg)}' is not a type")

            if issubclass(typearg, IO):
                if issubclass(value, IO_type_refs.get(typespec, object)):
                    return
                raise TypecheckError("{value!r:.100} is not a subclass of {exptype}",
                                     value=value, exptype=typearg, varname=argname)

            if issubclass(value, typearg):
                return
            raise TypecheckError("{value!r:.100} is not a subclass of {exptype}",
                                 value=value, exptype=typearg, varname=argname)

        # `Match` object conceals its type in `.string` attribute
        if typespec._name == 'Match':
            value: Match
            return _check_type_(value.string, typeargs[0], argname=argname)

        # `Pattern` object conceals its type in `.pattern` attribute
        if typespec._name == 'Pattern':
            value: Pattern
            return _check_type_(value.pattern, typeargs[0], argname=argname)


if __name__ == '__main__':
    @check_args
    def f(a: Type[List] = None, b: Iterable = 'e'):
        print(f'{a = }, {b = }')

    f(list, [])
