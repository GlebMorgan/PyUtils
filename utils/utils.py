from __future__ import annotations

import re
from contextlib import nullcontext
from enum import Enum
from itertools import islice, repeat, zip_longest
from operator import attrgetter
from subprocess import run
from typing import NamedTuple, TypeVar, Dict, Tuple
from typing import Any, Callable, Iterable, Iterator, Type, List, Collection, Literal, Union

from wrapt import decorator


# TODO: short module description, purpose

# FEATURE: listattrs() function, probably separate from Filter class
# CONSIDER: listattrs() coloring attrs based on type (method, function, dict attr, inherited attr, etc.)
#     listattrs goes to filters.py <= it depends on Filter class a lot

# FEATURE: console color-print module for Windows based on colorama – colors
#   color toggle to allow for clean output for terminals that does not support colors for some reason
#   implement support for indented levels of output, like `pip install` logging uses
#   >>> from utils.colors import print
#   >>> print('Some text')  # when just called, aliases built-in print()
#   >>> print['red']('Some text')  # uses __class_getattr__
#   >>> print.green('Some text')

# FEATURE: colored logging module with custom handlers and indented levels system
#   base scratch to start from – old PyUtils colored_logger.py

# FEATURE: classtools wrapper around pydantic or similar


__all__ = [
    'test', 'bytewise', 'bitwise', 'deprecated', 'autorepr', 'schain', 'isdunder', 'issunder', 'isiterable',
    'spy', 'Disposable', 'getter', 'setter', 'legacy', 'stack', 'Dummy', 'null', 'clipboard', 'ignore',
    'classproperty', 'Tree', 'AttrEnum',
]


class test:
    """Sample collections namespace class"""

    # Simple collections
    dict = dict(a=0, b=True, c='item', d=42, e=..., f=1.0, g=None, h=(1, 2, 3))
    list = [*dict.values()]
    set = {*list}

    # Number collections
    ndict = {i: f'item{i}' for i in range(10)}
    nlist = [*ndict.keys()]
    nset = {*nlist}

    # String collections
    sdict = {
        'beautiful': 'better than ugly',
        'explicit': 'better than implicit',
        'simple': 'better than complex',
        'complex': 'better than complicated',
        'flat': 'better than nested',
        'sparse': 'better than dense',
        'readability': 'counts',
        'practicality': 'beats purity',
        'errors': 'never passed silently',
        'namespaces': 'one honking great idea',
    }
    slist = [*sdict.keys()]
    sset = {*slist}

    # Mixed-type collections
    mdict = {
        1: 'a',
        2: 'b',
        3: 'c',
        'None': None,
        'bool': True,
        'str': 'python',
        'lstr': 'long example string that presumably have little chances '
                'to fit onto one single line (unless you use 4K monitor :)',
        'mstr': '1st str' + '\\n' + '2nd str',
        'ellipsis': ...,
        'list': [1, 2, 3, 4, 5, ('a', 'b', 'c'), ..., None],
        'empty': [],
        'tuple': tuple(range(12)),
        'dict': {1: 'first', 2: 'second'},
        'object': object(),
        'class': RuntimeError,
        'function': print,
        'module': re,
    }
    mlist = [*mdict.values()]
    mset = {item for item in mlist if item.__hash__}

    # Mixed-type collections with self-reference
    selfdict = dict.copy();  selfdict['self'] = selfdict
    selflist = [*dict.values()];  selflist.append(selflist)
    # NOTE: `selfset` does not exist due to self-reference is unhashable

    # Names of all collections defined
    all = [name for name in locals() if name[0] != '_']


def bytewise(byteseq: bytes, sep: str = ' ', limit: int = None, show_len: bool = True) -> str:
    """
    Return string representation of `byteseq` as hexadecimal uppercase octets separated by `sep`
    Functionally is the inverse of `bytes.fromhex()`
    In case the length of `byteseq` exceeds the value of specified `limit` argument, extra part of
        output is collapsed to an ellipsis and only the last element is shown after it (see example)
    If output is trimmed, `show_len` argument tells whether '(`<n>` bytes)' is appended to output
    Raises `ValueError` if `limit` is less than 2
    >>> assert bytewise(b'12345', sep='-') == '31-32-33-34-35'
    >>> assert bytewise(bytes.fromhex('00 01 42 5A FF')) == '00 01 42 5A FF'
    >>> assert bytewise(b'python', limit=5) == '70 79 74 .. 6E (6 bytes)'
    """

    octets = map(''.join, zip(*repeat(iter(byteseq.hex().upper()), 2)))
    if limit is None or len(byteseq) <= limit:
        return sep.join(octets)
    if limit < 2:
        raise ValueError("cannot limit sequence to less than 2 bytes")
    else:
        head = islice(octets, limit - 2)  # account for last byte + '..'
        last = byteseq[-1:].hex().upper()
        appendix = f' ({len(byteseq)} bytes)' if show_len else ''
        return sep.join((*head, '..', last)) + appendix


def bytewise2(byteseq: bytes, sep: str = ' ', limit: int = None, show_len: bool = True) -> str:
    """More readable, but 2.5 times slower implementation of `bytewise()`"""

    octets = (f'{byte:02X}' for byte in byteseq)
    if limit is None or len(byteseq) <= limit:
        return sep.join(octets)
    if limit < 2:
        raise ValueError("cannot limit sequence to less than 2 bytes")
    else:
        head = islice(octets, limit - 2)
        last = f'{byteseq[-1]:02X}'
        appendix = f' ({len(byteseq)} bytes)' if show_len else ''
        return sep.join((*head, '..', last)) + appendix


def bitwise(byteseq: bytes, sep: str = ' ') -> str:
    """
    Return string representation of `byteseq` as binary octets separated by `sep`
    >>> assert bitwise(b'abc') == '01100001 01100010 01100011'
    >>> assert bitwise(bytes.fromhex('00 0A FF')) == '00000000 00001010 11111111'
    """
    return sep.join(f"{byte:08b}" for byte in byteseq)


def deprecated(reason: str):
    """
    Issue `DeprecationWarning` before invoking the wrapee function
    Note: Warning filters should be enabled in order for the warning to be displayed.
        Minimal required filter is 'default::DeprecationWarning:utils'
    If `reason` argument is specified, it will be displayed after the warning message
    >>> @deprecated('duck tape')
    ... def func(): ...
    ...
    >>> func()
    DeprecationWarning: Function 'func' is marked as deprecated (duck tape)
    """

    @decorator
    def deprecation_wrapper(wrapped, instance, args, kwargs):
        from warnings import warn
        nonlocal details
        wrapee = wrapped.__class__.__name__.replace('type', 'class')
        message = f"{wrapee.capitalize()} '{wrapped.__name__}' is marked as deprecated"
        if details:
            message += f' ({details})'
        warn(message, category=DeprecationWarning, stacklevel=3)
        return wrapped(*args, **kwargs)

    if isinstance(reason, str):
        # Infer decorator is used with an argument,
        #   thus store `reason` in a closure from `deprecation_wrapper`
        details = reason
        return deprecation_wrapper
    else:
        # Infer decorator is used without arguments,
        #   in this case `reason` is expected to be an object to be wrapped
        details = ''
        return deprecation_wrapper(reason)


def autorepr(msg: str) -> Callable[[Any], str]:
    """
    Generate canonical `__repr__()` method using provided `msg`
    >>> class Belarus:
    ...     __repr__ = autorepr('deserves respect')
    ...
    >>> repr(Belarus)
    "<utils.autorepr.<locals>.Belarus deserves respect at 0x...>"
    """

    def __repr__(self):
        cls = self.__class__
        return f"<{cls.__module__}.{cls.__qualname__} {msg} at {hex(id(self))}>"
    return __repr__


def schain(*items):
    """
    SmartChain – extended `itertools.chain()`
      • accepts singular objects as well as iterables
      • treats `str` as items, not iterables
    >>> assert [*schain(-1, range(3), 8)] == [-1, 0, 1, 2, 8]  # accepts non-iterable objects
    >>> assert [*schain(('foo', 'bar'), 'solid')] == ['foo', 'bar', 'solid'] # does not tear strings apart
    >>> assert [*schain(range(3), 3, [], 42)] == [0, 1, 2, 3, 42]  # iterables and items could go in any order
    """
    for item in items:
        if isinstance(item, str):
            yield item
        elif hasattr(item, '__iter__'):
            yield from item
        else:
            yield item


def isdunder(name: str) -> bool:
    """Return whether `name` is a __double_underscore__ name (from enum module)"""
    return (name[:2] == name[-2:] == '__' and
            name[2:3] != '_' and name[-3:-2] != '_' and
            len(name) > 4)


def issunder(name):
    """Return whether `name` is a _single_underscore_ name"""
    return (name[:1] == name[-1:] == '_' and
            name[1:2] != '_' and name[-2:-1] != '_' and
            len(name) > 2)


def isiterable(obj) -> bool:
    """Return whether `obj` is iterable, considering `str` and `bytes` are not"""
    if isinstance(obj, (str, bytes)):
        return False
    else:
        return isinstance(obj, Iterable)


class Disposable:
    """
    Descriptor that clears its value after each access
    >>> class Class:
    ...     attr = Disposable(100500)
    ...
    >>> obj = Class()
    >>> assert obj.attr == 100500  # returns initial value
    >>> obj.attr = 42  # descriptor value is set to 42
    >>> assert obj.attr == 42  # first access returns value
    >>> assert obj.attr is None  # subsequent access returns None
    """

    def __init__(self, value=None):
        self.value = value

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = self.value
        self.value = None
        return value

    def __set__(self, instance, value):
        self.value = value


class spy:
    """
    Iterator around given iterable with separate independent iterator branch for lookahead
    `.lookahead()` returns an iterator that advances the underlying iterable,
        but does not influence on main iteration branch
    `spy` object itself works just as conventional iterable regardless of `.lookahead()` state
    >>> iterator = spy(range(1, 3))  # spy object wraps range(5)
    >>> lookahead = iterator.lookahead()  # independent lookahead iterator is created
    >>> assert lookahead.__next__() == 1
    >>> assert iterator.__next__() == 1
    >>> assert list(lookahead) == [2, 3]
    >>> assert list(iterator) == [2, 3]
    >>> assert list(lookahead) == []  # exhausted
    """

    def __init__(self, iterable):
        self.source = iter(iterable)
        self.cache = []

    def __iter__(self):
        return self

    def __next__(self):
        if self.cache:
            return self.cache.pop(0)
        else:
            return next(self.source)

    def lookahead(self) -> Iterator:
        for item in self.source:
            self.cache.append(item)
            yield item


class GetterDescriptor:
    """
    Decorator implementing getter-only attribute descriptor
    Wraps given getter function into descriptor object that uses its return value when
        instance attribute with the same name as was assigned to descriptor itself is acessed
    Attribute setting and deletion procedures are left unaffected
    Signature of decorated getter method should be `getter(self, value) -> returned`:
        • `value` – the actual value of requested instance attribute stored in instance `__dict__`
        • `returned` – getter return value that is to be returned to outer code requesting the attribute
    >>> class GetterExample:
    ...     @getter
    ...     def attr(self, value):
    ...         # handle acquired value somehow...
    ...         return str(value)
    ...
    >>> instance = GetterExample()
    >>> instance.attr = 42
    >>> assert instance.__dict__['attr'] == 42  # store unchanged
    >>> assert instance.attr == '42'  # acquire modified
    """

    # NOTE: __slots__ break dynamic docstrings

    def __init__(self, method):
        self.name: str
        self.getter = method
        self.__doc__ = method.__doc__

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            value = instance.__dict__[self.name]
        except KeyError:
            message = f"'{instance.__class__.__name__}' object has no attribute '{self.name}'"
            raise AttributeError(message) from None
        return self.getter(instance, value)

    def __set__(self, instance, value):
        # Required to make the class a data descriptor
        instance.__dict__[self.name] = value


class SetterDescriptor:
    """
    Decorator implementing setter-only attribute descriptor
    Wraps given setter function into descriptor object that assigns its return value
        to instance attribute with the same name as was assigned to descriptor itself
    Attribute access and deletion procedures are left unaffected
    Signature of decorated setter method should be `setter(self, value) -> stored`:
        • `value` – the value being set to instance attribute from outer code
        • `stored` – return value that is to be actually assigned to instance attribute
    >>> class SetterExample:
    ...     @setter
    ...     def attr(self, value):
    ...         # handle reassignment somehow...
    ...         return str(value)
    ...
    >>> instance = SetterExample()
    >>> instance.attr = 42
    >>> assert instance.__dict__['attr'] == '42'  # store modified
    >>> assert instance.attr == '42'  # acquire unchanged
    """

    # NOTE: __slots__ break dynamic docstrings

    def __init__(self, method):
        self.name: str
        self.setter = method
        self.__doc__ = method.__doc__

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        instance.__dict__[self.name] = self.setter(instance, value)


getter = GetterDescriptor
setter = SetterDescriptor


def legacy(function):
    """
    Decorator to mark wrapped function or method is out of use
    Returns new function that raises `RuntimeError` when called
    """
    def wrapper(*args, **kwargs):
        obj_type: str = function.__class__.__name__.replace('type', 'class')
        raise RuntimeError(f"{obj_type} '{function.__name__}' is marked as legacy")
    return wrapper


def stack(iterable, *, indent=4):
    """Print iterable in a column"""
    whitespace = ' '*indent
    if isinstance(iterable, dict):
        items = (f'{whitespace}{key}: {item}' for key, item in iterable.items())
    else:
        items = (f'{whitespace}{item}' for item in iterable)
    print('\n'.join(items))


class Dummy:
    """
    Mock no-op class returning itself on every attr access or method call
    Intended for avoiding both if-checks and attribute errors when dealing with objects
    Evaluates to False on logical operations
    >>> dummy = Dummy('whatever', accepts='any args')
    >>> assert str(dummy) == 'Dummy'
    >>> assert dummy.whatever is dummy
    >>> assert dummy.method('any', 'args') is dummy
    >>> assert dummy('any', 'args') is dummy
    >>> assert bool(dummy) is False
    """

    def __init__(self, *args, **kwargs):
        pass

    def __str__(self):
        return self.__class__.__name__

    __repr__ = autorepr('object')

    def __getattr__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return False


class NullType:
    """
    Sentinel object for denoting the absence of a value
    Should not be used as a distinct value for some attribute or variable
    """

    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        return null

    def __str__(self):
        return 'N/A'

    def __repr__(self):
        return f"<Null object at {hex(id(self))}>"

    def __bool__(self):
        return False


null = object.__new__(NullType)


def clipboard(text: str):
    """
    Put given string into Windows clipboard
    Raises `subprocess.CalledProcessError` if underlying `clip` utility returns non-zero exit code
    """
    run(f'echo | set /p nul={text.strip()}| clip', check=True)


class ignore:
    """
    Context manager for filtering specified errors
    Accepts any amount of exception types, subclasses are respected
    If no error type is provided, returns nullcontext that does nothing –
        that simplifies usage in case exception types are calculated dymamically

    >>> with ignore(LookupError):
    ...     raise KeyError()  # KeyError is a subclass of LookupError, so it is filtered out
    ...

    >>> with ignore(LookupError):
    ...     raise RuntimeError('message')  # RuntimeError does not pass a filter, so it is raised
    ...
    RuntimeError: message
    >>> with ignore():
    ...     raise Exception('message')  # no exception types are being passed, so nothing is filtered
    ...
    Exception: message
    """

    def __new__(cls, *args):
        if args == ():
            return nullcontext()
        return super().__new__(cls)

    def __init__(self, *error_types: Type[Exception]):
        self.exctypes = error_types

    def __enter__(self):
        pass

    def __exit__(self, exctype, exc, traceback):
        return isinstance(exc, self.exctypes)


class classproperty:
    """Decorator implementing a class-level read-only property"""

    def __init__(self, method: Callable):
        self.getter = method
        self.__doc__ = method.__doc__

    def __get__(self, instance, owner=None):
        return self.getter(owner or type(instance))


class Tree:
    """
    Tree structure converter and tree-style renderer
    Intended to be used mainly for display purposes
    Does not handle cycle references for now
    >>> exceptions = [...]  # list of all python exceptions
    >>> tree = Tree.build(items=exceptions, naming='__name__', parents='__base__')
    >>> assert str(tree) == tree.render()
    >>> tree.render()
    object
    └── BaseException
        ├── Exception
        │   ├── ArithmeticError
        │   │   ├── FloatingPointError
        │   │   ├── OverflowError
        │   │   └── ZeroDivisionError
        │   ├── AssertionError
        │   ├── AttributeError
        ...
    """

    Item = TypeVar('Item')
    NameHandle = Callable[[Item], str]
    ParentHandle = Callable[[Item], Item]
    ChildrenHandle = Callable[[Item], Collection[Item]]

    class Node(NamedTuple):
        name: str  # string used for node representation when rendering a tree
        value: Tree.Item  # actual item, aka tree node payload
        nodes: List[Tree.Node]  # list of children nodes

    # Dict[stylename: (line, fork, end, void)]
    marker_styles: Dict[str, Tuple[str, str, str, str]] = {
        'strict': ('│   ', '├── ', '└── ', '    '),
        'smooth': ('│   ', '├── ', '╰── ', '    '),
        'indent': ('    ',) * 4,
    }

    def __init__(self, root: Node):
        self.root = root

    def __str__(self):
        return self.render()

    def render(self, style: Literal['strict', 'smooth', 'empty'] = 'strict', empty: str = '<Empty tree>'):
        """
        Create tree-like visual representation string
        Strings used for visualising tree branches are determined by 'style' argument
        Empty tree representation is specified by 'empty' argument
        """

        if style not in self.marker_styles.keys():
            styles = ', '.join(self.marker_styles.keys())
            raise ValueError(f"invalid style: expected [{styles}], got {style!r}")

        if not self.root:
            return empty

        line, fork, end, void = self.marker_styles[style]

        def generate(nodes: List[Tree.Node], prefix: str = ''):
            last = len(nodes)-1
            for i, item in enumerate(nodes):
                yield f'{prefix}{end if i is last else fork}{item.name}'
                if item.nodes:
                    yield from generate(item.nodes, prefix+(void if i is last else line))

        return '\n'.join(schain(self.root.name, generate(self.root.nodes)))

    @classmethod
    def convert(cls, root: Item, naming: Union[str, NameHandle], children: Union[str, ChildrenHandle]) -> Tree:
        """
        Build the tree starting from given root item top-down following references to child nodes
        The name for each generated node is determined by 'naming' argument, which can be:
            • string – defines the name of an item's attribute, so that `node.name = item.<name>`
            • callable – defines a callable of a single argument, so that `node.name = <callable>(item)`
        Similarly, 'children' argument defines a handle for acquiring a list of item's children.
            It could be whether a item's attribute name or a single-argument callable hook
        """

        def get_children(node: cls.Item) -> List[cls.Node]:
            children_nodes = children_handle(node)
            if children_nodes is None:
                return []
            if not isinstance(children_nodes, Collection):
                err_msg = f'children handle returned invalid result: expected List[Item], got {children_nodes!r}'
                raise RuntimeError(err_msg)
            return [cls.Node(name=name_handle(child), value=child, nodes=get_children(child))
                    for child in children_nodes]

        children_handle = attrgetter(children) if isinstance(children, str) else children
        name_handle = attrgetter(naming) if isinstance(naming, str) else naming

        return cls(cls.Node(name=name_handle(root), value=root, nodes=get_children(root)))

    @classmethod
    def build(cls, items: Iterable[Item], naming: Union[str, NameHandle],
              parent: Union[str, ParentHandle] = None) -> Tree:
        """
        Build the tree out of collection of items bottom-up following references to parent nodes
        Semantics of `naming` and `parents` arguments is similar to corresponding arguments of `.convert()` method
        Elements of `items` collection should be hashable
        """

        parent_handle = attrgetter(parent) if isinstance(parent, str) else parent
        name_handle = attrgetter(naming) if isinstance(naming, str) else naming

        nodes_index = {}
        root = None
        for item in items:
            if item in nodes_index:
                continue
            node = cls.Node(name=name_handle(item), value=item, nodes=[])
            nodes_index[item] = node
            parent_item = parent_handle(item)
            while parent_item not in nodes_index:
                if parent_item is None:
                    if root is None:
                        root = node
                        break
                    else:
                        err_msg = f"Given collection of items is not a connected graph! " \
                                  f"Both {root.value!r} and {parent_item!r} nodes does not have a parent"
                        raise RuntimeError(err_msg)
                parent_node = cls.Node(name=name_handle(parent_item), value=parent_item, nodes=[node])
                nodes_index[parent_item] = parent_node
                node = parent_node
                parent_item = parent_handle(parent_item)

            if parent_item:
                nodes_index[parent_item].nodes.append(node)

        for node in nodes_index.values():
            node.nodes.sort(key=attrgetter('name'))

        return cls(root)


class AttrEnum(Enum):
    """
    Enum with custom attributes + an automatic `.index` attribute
    `AttrEnum` attributes are declared by assigning desired names to special `__fields__` variable
        on the very first line of enum class body (somewhat similar to Python `__slots__`)
    Attribute values are set by assigning each `AttrEnum` member with a tuple of values,
        that correspond to specified `__fields__`; missing values fallback to `None`
    Attribute `.index` is set automatically and defaults to enum member index number within order of declaration
    Both `.value` and `.index` attributes may be overridden by providing their names in `__fields__`
    If `__fields__` tuple is not specified, only `.index` attribute is added to enum member implicitly;
        besides that the class would generally behave like conventional `Enum`

    >>> class Sample(AttrEnum):
    ...     __fields__ = 'attr1', 'attr2', 'attr3'
    ...     A = 'data_A', 10, True
    ...     B = 'data_B', 42
    ...     C = 'data_C', 77
    ...
    >>> member = Sample.B
    >>> assert member.name == 'B'
    >>> assert member.index == 1  # counts from 0 in order of declaration
    >>> assert member.value == ('data_B', 42, None)  # values are filled up to match __fields__
    >>> assert member.attr1 == 'data_B'
    >>> assert member.attr2 == 42
    >>> assert member.attr3 is None  # if attr is not specified, it defaults to None
    >>> assert repr(member) == "<Sample.B: attr1='data_B', attr2=42, attr3=None>"

    >>> class ValueSample(AttrEnum):
    ...     __fields__ = 'index', 'value'
    ...     A = 1, 'data_A'
    ...     B = 3, 'data_B'
    ...     C = 2, 'data_C'
    ...
    >>> member = ValueSample.B
    >>> assert member.name == 'B'
    >>> assert member.index == 3  # index is overridden
    >>> assert member.value == 'data_B'  # value is overridden as well
    >>> assert repr(member) == "<ValueSample.B: index=3, value='data_B'>"  # repr keeps unified format

    >>> class VoidSample(AttrEnum):
    ...     A = 2
    ...     B = 7
    ...     C = 9
    ...
    >>> member = VoidSample.B
    >>> assert member.name == 'B'
    >>> assert member.index == 1  # .index defaults to enum member index number
    >>> assert member.value == 7  # .value defaults to whatever member is assigned to
    >>> assert repr(member) == "<VoidSample.B: 7>"
    """

    # CONSIDER: support single string __fields__

    __fields__: tuple = ()

    def __new__(cls, *args):
        obj = object.__new__(cls)

        # If __fields__ are not provided, just set .index
        #   and leave .value to be defined by Enum internals
        if not cls.__fields__:
            obj.index = len(cls.__members__)
            return obj

        # Deny reserved names
        # (this check is performed redundantly during creation of each enum member,
        #   but adding a custom metaclass for performing it just once does not seem like a wonderful idea)
        for name in cls.__fields__:
            if name.startswith('_') or name.endswith('_') or name == 'name':
                raise ValueError(f"invalid field name '{name}'")

        # Freak out if specified member attrs exceed number of fields
        if len(args) > len(cls.__fields__):
            err_msg = "enum member has too many attrs: expected {n_fields}, got {n_args}"
            raise ValueError(err_msg.format(n_fields=len(cls.__fields__), n_args=len(args)))

        # Assign .value and .index with values from attrs, or defaults if not provided
        attrs: dict = dict(zip_longest(cls.__fields__, args))
        obj._value_ = attrs.pop('value', tuple(attrs.values()) if len(attrs) > 1 else args[0])
        obj.index = attrs.pop('index', len(cls.__members__))

        # Set specified attrs
        obj.__dict__.update(attrs)

        return obj

    def __repr__(self):
        if self.__fields__:
            attrs = ', '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__fields__)
        else:
            attrs = repr(self._value_)
        return f'<{self.__class__.__name__}.{self._name_}: {attrs}>'

    def __str__(self):
        return f'{self.__class__.__name__}.{self._name_}'

    def __dir__(self):
        fields = (name for name in self.__fields__ if name not in ('index', 'value'))
        return *super().__dir__(), '__fields__', 'index', *fields
