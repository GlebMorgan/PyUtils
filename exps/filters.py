"""
Module intended for creating print filters for Python interactive sessions
Usage: `some_object |<filter>`
Example:
>>> [0, 'string', range(3)] |show

"""

import os
import sys
from enum import Enum
from functools import partial
from itertools import islice
from math import log10
from textwrap import TextWrapper
from types import GeneratorType
from typing import Union, Iterator, Iterable, Mapping, Tuple, Collection, Callable, Optional, Dict, Any

from utils.typechecking import check_args
from utils.utils import spy, schain, setter


# TODO: handle self-references (at least, on level 1)

# TODO: add option to insert number of items in every representation method that strips iterable in any way

# TODO: reimplement 'limit' and 'nested' to account for amount of lines, not items
#   (gonna be hard to implement since TextWrapper objects manipulate strings, not str iterators)

# TODO: option to specify an error to raise when typechecking

# CONSIDER: class Describe(Format) – alternative implementation of simpler listattrs() function)


Items = Union[Iterable, Collection]


class OptionError(ValueError):
    """Invalid value is provided to `Format` option"""

    def __init__(self, name, expected, actual):
        message = f"invalid value for option '{name}': expected {expected}, got {actual!r:.100}"
        super().__init__(message)


class Mode(Enum):
    """Display method for expandable objects"""
    stack = "arrange elements vertically so that each element takes its own line"
    inline = "arrange elements horizontally, wrap onto lines below if they do not fit on a single line"
    smart = "inline if elements fit on a single line, else stack or wrap based on their average width"
    trim = "force elements to take up a single line, truncate those which do not fit"
    stub = "show simple stub, do not display contents"
    native = "show native representation with no respect of specified width"


def get_default_width(fallback: int) -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return fallback


class Format:
    """
    TODO: Proper docstring
    Format given collection or iterable recursively expanding each nested iterable element
    Output is justified to specified `width`
    Expanded items are indented to specified level, determined by `indent` option
    Nested iterables treatment is determined by `mode` option
    What types of objects should be expanded is determined by `expandables` option
    Recursion level, output limit, serialization function, enumerators
        and other parameters are customized too
    API function to use is `.format()`
    """

    # TODO: help

    designators = {
        dict: ('{', '}'),
        list: ('[', ']'),
        tuple: ('(', ')'),
        set: ('<', '>'),
        GeneratorType: ('((', '))'),
    }

    @check_args('limit', 'nested', 'indent', 'repr', 'small', 'expandables', 'en_list', 'en_dict', 'en_tuple', 'en_set')
    def __init__(self,
                 width: int = get_default_width(fallback=132),  # maximum width for the generated output
                 limit: Optional[int] = None,  # display limit for the first-level iterable
                 nested: Optional[int] = 25,  # display limit for nested iterables
                 indent: int = 4,  # indentation size (N of spaces)
                 mode: Union[str, Mode] = Mode.smart,  # 0-level mode is always 'stack'
                 recurse: Union[bool, int] = True,  # max recursion level
                 repr: Callable[[Any], str] = str,  # function used to serialize items
                 linesep: str = '|',  # line delimiter for single-line modes (single-character)
                 small: int = 10,  # maximum average item representation size to inline elements in 'smart' mode
                 brackets: Union[bool, str] = True,  # show brackets around iterables
                 empty: Optional[Callable[[Iterable], str]] = None,  # empty sequence display method
                 expandables: Tuple[type, ...] = (dict, set, list, tuple),
                 en_list: str = r'{:0\w}. ',  # list enumerator template
                 en_dict: str = r'{}: ',  # dict enumerator template
                 en_tuple: str = '- ',  # tuple enumerator template
                 en_set: str = '• ',  # set enumerator template
                 ):

        self.width: int = width
        self.limit: Optional[int] = limit
        self.nested: Optional[int] = nested
        self.indent: int = indent
        self.mode: Mode = mode
        self.recurse: int = recurse
        self.repr: Callable[[Any], str] = repr
        self.linesep: str = linesep
        self.small: int = small
        self.brackets: Union[bool, Tuple[str, str]] = brackets
        self.empty: Callable[[Iterable], str] = empty
        self.expandables: Tuple[type, ...] = expandables
        # ▼ enumerator format for 'stack' mode; '\w' will be replaced with appropriate width dynamically
        self.enumerators: Dict[type, str] = {list: en_list, dict: en_dict, tuple: en_tuple, set: en_set}

        self.multiline_wrapper = TextWrapper(tabsize=4, placeholder='...', width=width)
        self.singleline_wrapper = TextWrapper(tabsize=4, placeholder='...', width=width)
        self.inline_wrapper = TextWrapper(tabsize=4, placeholder='...', width=width)

    @setter
    def width(self, value: Optional[int]) -> int:
        if value is None:
            new_width = os.get_terminal_size().columns
        elif not isinstance(value, int) or value < 0:
            raise OptionError(name='width', expected='positive int or None', actual=value)
        else:
            new_width = value
        try:
            self.multiline_wrapper.width = new_width
            self.singleline_wrapper.width = new_width
            self.inline_wrapper.width = new_width
        except AttributeError:
            pass
        return new_width

    @setter
    def mode(self, value: Union[str, Mode]) -> Mode:
        if isinstance(value, str):
            if value not in Mode.__members__.keys():
                member_names = ', '.join(member.name.join("''") for member in Mode)
                raise OptionError(name='mode', expected=f"[{member_names}]", actual=value)
            return Mode[value]
        elif isinstance(value, Mode):
            return value
        else:
            raise OptionError(name='mode', expected='Mode enum member or a string', actual=value)

    @setter
    def recurse(self, value: Union[bool, int]) -> int:
        if value is True:
            return sys.maxsize
        elif value is False:
            return 0
        elif not isinstance(value, int) or value < 0:
            raise OptionError(name='recurse', expected='positive int or bool', actual=value)
        else:
            return value

    @setter
    def linesep(self, value: str) -> str:
        if not isinstance(value, str) or len(value) > 1:
            raise OptionError(name='recurse', expected='single-character str', actual=value)
        return value

    @setter
    def brackets(self, value: Union[bool, str]) -> Union[bool, Tuple[str, str]]:
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value[:-1], value[-1]
        else:
            raise OptionError(name='brackets', expected='string with brackets or bool', actual=value)

    @setter
    def empty(self, value: Optional[Callable[[Iterable], str]]) -> Callable[[Iterable], str]:
        if value is None:
            return lambda iterable: f'<empty {iterable.__class__.__name__}>'
        elif callable(value):
            return value
        else:
            raise OptionError(name='empty', expected="None or a callable", actual=value)

    def _set_enumerator_(self, container_type: type, value: Optional[str]):
        if not isinstance(value, str):
            raise OptionError(name=f'en_{container_type.__name__}', expected='str', actual=value)
        self.enumerators[container_type] = value or ''

    en_dict = property(fset=partial(_set_enumerator_, dict))
    en_list = property(fset=partial(_set_enumerator_, list))
    en_tuple = property(fset=partial(_set_enumerator_, tuple))
    en_set = property(fset=partial(_set_enumerator_, set))
    en_gen = property(fset=partial(_set_enumerator_, GeneratorType))

    def _get_brackets_(self, iterable: Items) -> Tuple[str, str]:
        if self.brackets is True:
            iterable_type = iterable.__class__
            return self.designators.get(iterable_type, (iterable_type.__name__ + '(', ')'))
        elif self.brackets is False:
            return '', ''
        else:
            return self.brackets

    # @legacy
    # def _get_brackets_(self, content_type) -> Tuple[str, str]:
    #     if self.brackets is True:
    #         brackets = next((value for key, value in self.designators.items() if issubclass(content_type, key)), None)
    #         if brackets is not None:
    #             return brackets
    #         else:
    #             return content_type.__name__ + '(', ')'
    #     if not self.brackets:
    #         return '', ''
    #     if isinstance(self.brackets, str):
    #         return self.brackets[:-1], self.brackets[-1]
    #     else:
    #         return self.brackets

    # @legacy
    # def _format_empty_(self, iterable: Items) -> str:
    #     if self.empty is True:
    #         return f'<empty {iterable.__class__.__name__}>'
    #     elif self.empty is False:
    #         return str(iterable)
    #     elif self.empty is None:
    #         return ''
    #     elif callable(self.empty):
    #         return self.empty(type(iterable))
    #     else:
    #         return self.empty

    # @legacy  # _format_ is acquired as getattr(self, f'_{self.mode.name}_')
    # def _format_inner_(self, iterable: Items, indented: int = 0, level: int = 0) -> str:
    #     """
    #     Dispatched dynamically
    #     """
    #     return NotImplemented

    def _smart_(self, iterable: Items, indented: int = 0, level: int = 0) -> str:
        brackets = self._get_brackets_(iterable)
        available_width = self.width - indented - (len(brackets[0]) + len(brackets[1]))
        size_limit = self.limit if level == 0 else self.nested

        if isinstance(iterable, Mapping):
            iterator = (f'{key}: {self.repr(item)}' for key, item in iterable.items())
        elif isinstance(iterable, Collection):
            iterator = map(self.repr, iterable)
        else:
            iterable = spy(iterable)
            iterator = map(self.repr, iterable.lookahead())

        buffered = []
        size = -2  # compensate for the absence of ', ' before the first item
        for n, item in enumerate(islice(iterator, size_limit), start=1):
            buffered.append(item)
            size += len(item) + 2  # account for ', '
            # If does not fit on a single line
            if size > available_width:
                # Average item representation size exceeds the threshold - go with 'inline' mode
                if size/n <= self.small:
                    return self._inline_(iterable, indented, level)
                # Item representation takes too much space on average - go with 'stack' mode
                else:
                    return self._stack_(iterable, indented, level)

        # Fits on a single line - go with it
        # TODO: replace with Null or even with isconsumed()
        exhausted = object()
        if next(iterator, exhausted) is not exhausted:
            buffered.append('...')
        return ', '.join(buffered).replace('\n', self.linesep).join(brackets)

    def _stack_(self, iterable: Items, indented: int = 0, level: int = 0) -> str:
        if not iterable:
            return self.empty(iterable)
        if self.brackets is not False:
            brackets = self._get_brackets_(iterable)
            indent = ' ' * self.indent * level
            return '\n'.join(schain(brackets[0], self.stack(iterable, level), indent+brackets[1]))
        else:
            return '\n'.join(self.stack(iterable, level))

    def _inline_(self, iterable: Items, indented: int = 0, level: int = 0) -> str:
        """
        Enumerators are not applied, no nesting
        """
        whitespace = ' ' * self.indent * (level + 1)
        brackets = self._get_brackets_(iterable)
        size_limit = self.limit if level == 0 else self.nested

        if isinstance(iterable, Mapping):
            iterator = iter(iterable.items())
            content = ', '.join(f'{key}: {self.repr(item)}' for key, item in islice(iterator, size_limit))
        else:
            iterator = iter(iterable)
            content = ', '.join(self.repr(item) for item in islice(iterator, size_limit))

        # TODO: replace with Null or even with isconsumed()
        exhausted = object()
        if next(iterator, exhausted) is not exhausted:
            content += ', ...'

        content.replace('\n', self.linesep)
        full_line = ''.join(('#'*indented, brackets[0], content, brackets[1]))
        self.inline_wrapper.subsequent_indent = whitespace
        return self.inline_wrapper.fill(full_line)[indented:]

    def _trim_(self, iterable: Items, indented: int = 0, level: int = 0) -> str:
        brackets = self._get_brackets_(iterable)
        available_width = self.width - indented - (len(brackets[0]) + len(brackets[1]))

        items_buffer = []
        size = -2  # compensate for the absence of ', ' before the first item
        for item in iterable:
            item_repr = self.repr(item)
            size += len(item_repr) + 2  # account for ', '
            items_buffer.append(item_repr)
            if size > available_width:
                # iterable does not fit into available width - remove items until able to add ', ...'
                postfix = ', ...'
                for i in range(3):
                    last = items_buffer.pop()
                    size -= len(last) + 2
                    if size + len(postfix) <= available_width:
                        break  # stop removing elements from items buffer
                break
        else:
            # iterable fits into available width - do not add ellipsis
            postfix = ''

        result = ', '.join(items_buffer).replace('\n', self.linesep) + postfix
        return result.join(brackets)

    # @legacy
    # def _trim_(self, buffered: List[str], brackets: Tuple[str, str], width: int):
    #     for _ in range(len(buffered)):
    #         last = buffered.pop()
    #         if sum(map(len, buffered)) + 5 <= width:
    #             return ', '.join(schain(buffered, '...')).replace('\n', self.linesep).join(brackets)
    #     # noinspection PyUnboundLocalVariable
    #     if len(last) > width:
    #         return (last[:width-3] + '...').join(brackets)

    def _stub_(self, iterable: Items, indented: int = 0, level: int = 0) -> str:
        width = self.width - indented - 2  # account for '<>'
        msg = f'{iterable.__class__.__name__}'
        if isinstance(iterable, Collection):
            msg += f' ({len(iterable)} items)'
        if len(msg) > width:
            msg = msg[:width-3] + '...'
        return msg.join('<>')

    def _native_(self, iterable: Items, indented: int = 0, level: int = 0) -> str:
        width = self.width - indented
        result = self.repr(iterable)
        if len(result) > width:
            result = result[:width-4] + '...' + result[-1]
        return result

    def help(self):
        return self._stack_(self.__dict__)

    def stack(self, iterable: Items, level: int = 0) -> Iterator[str]:
        whitespace = ' ' * self.indent * (level + 1)
        indent = ' ' * self.indent
        size_limit = self.limit if level == 0 else self.nested
        template = self.enumerators.get(type(iterable), '')
        iterator = iter(iterable.items()) if isinstance(iterable, Mapping) else enumerate(iterable)

        if r'\w' in template:
            if isinstance(iterable, Mapping):
                enumerator_width = max(map(len, map(str, iterable.keys())))
            else:
                enumerator_width = int(log10(min(len(iterable), size_limit or sys.maxsize))) + 1
            template = template.replace(r'\w', str(enumerator_width))

        for i, item in islice(iterator, size_limit):
            prefix = whitespace + template.format(i)
            available_width = self.width - len(prefix)

            if isinstance(item, self.expandables):
                if level < self.recurse:
                    if item:
                        format_method = getattr(self, f'_{self.mode.name}_')
                        yield prefix + format_method(item, indented=len(prefix), level=level+1)
                    else:
                        yield prefix + self.empty(item)
                else:
                    yield prefix + self._native_(item, len(prefix), level=level+1)
            else:
                item_repr = self.repr(item)
                # Wrap onto multiple lines if item is itself a string
                if isinstance(item, str):
                    if len(item_repr) <= available_width:
                        yield prefix + item_repr.replace('\n', self.linesep)
                    elif '\n' in item_repr:
                        base_whitespace = ' ' * len(prefix)
                        self.multiline_wrapper.max_lines = size_limit
                        self.multiline_wrapper.initial_indent = base_whitespace
                        self.multiline_wrapper.subsequent_indent = base_whitespace + indent
                        result ='\n'.join(map(self.multiline_wrapper.fill, item_repr.splitlines()))
                        yield prefix + result[len(prefix):]
                    else:
                        self.singleline_wrapper.max_lines = size_limit
                        self.singleline_wrapper.subsequent_indent = whitespace + indent
                        yield self.singleline_wrapper.fill(prefix + item_repr)
                # Trim to fit available width if item is not itself a string
                elif len(item_repr) > available_width:
                    yield prefix + item_repr[:available_width-3] + '...'
                else:
                    yield prefix + item_repr

        # TODO: replace with Null or even with isconsumed()
        exhausted = object()
        if next(iterator, exhausted) is not exhausted:
            yield whitespace + '...'

    format = _stack_


class Show(Format):
    """
    Print output of Format.format() with `|show` syntax
    """

    def __ror__(self, operand):
        print(self.format(operand))

    def __call__(self, *args, **kwargs):
        return self.__class__(*args, **kwargs)


show = Show()
form = Format()


if __name__ == '__main__':
    from utils.utils import test
    d = test.mdict
    d['llist'] = [f'long item {i}' for i in range(12)]
    d['mllstr'] = 'first long line of words that does not necessarily fit onto a single line\n' \
                  'second not so short line that have certain chance of ' \
                  'not fitting within specified width as well\n' \
                  'third line that probably will fit'
    d['long_key_name'] = 'lol'*30
    d['marker_str'] = '- '*120

    d |show
