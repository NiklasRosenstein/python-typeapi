
import collections.abc
import sys
import typing as t

import pytest
from typeapi.api import Annotated, Any, ClassVar, Final, ForwardRef, Literal, NewType, NoReturn, Type, TypeGuard, Union, Unknown
from typeapi.parser import parse_type_hint
from utils import parametrize_typing_module

T = t.TypeVar('T')


def test_parser_type_hint_any():
  assert parse_type_hint(t.Any) == Any(t.Any)


@parametrize_typing_module('Annotated')
def test_parse_type_hint_annotated(m):
  assert parse_type_hint(m.Annotated[int, 42]) == Annotated(m.Annotated[int, 42], int, (42,))


def test_parse_type_hint_forward_ref():
  assert parse_type_hint('str') == ForwardRef('str', 'str', None)
  assert parse_type_hint(t.ForwardRef('str')) == ForwardRef(t.ForwardRef('str'), 'str', None)


def test_parse_type_hint_class_var():
  assert parse_type_hint(t.ClassVar) == Unknown(t.ClassVar)
  assert parse_type_hint(t.ClassVar[int]) == ClassVar(t.ClassVar[int], int)


@parametrize_typing_module('Final')
def test_parse_type_hint_final(m):
  assert parse_type_hint(m.Final) == Unknown(m.Final)
  assert parse_type_hint(m.Final[int]) == Final(m.Final[int], int)


def test_parse_type_hint_no_return():
  assert parse_type_hint(t.NoReturn) == NoReturn(t.NoReturn)


@parametrize_typing_module('TypeGuard')
def test_parse_type_hint_type_guard(m):
  assert parse_type_hint(m.TypeGuard) == Unknown(m.TypeGuard)
  assert parse_type_hint(m.TypeGuard[str]) == TypeGuard(m.TypeGuard[str], str)


def test_parse_type_hint_union():
  assert parse_type_hint(t.Union) == Unknown(t.Union)
  assert parse_type_hint(t.Union[int, str]) == Union(t.Union[int, str], (int, str))
  assert parse_type_hint(t.Optional[int]) == Union(t.Optional[int], (int, type(None)))
  assert parse_type_hint(t.Union[int, None, str]) == Union(t.Union[int, None, str], (int, type(None), str))


@pytest.mark.skipif(sys.version_info[:2] < (3, 10), reason='PEP 585 is implemented starting with Python 3.10')
def test_parse_type_hint_union_pep585():
  assert parse_type_hint(int | str) == Union(int | str, (int, str))
  assert parse_type_hint(int | None) == Union(int | None, (int, type(None)))
  assert parse_type_hint(int | None | str) == Union(int | None | str, (int, type(None), str))


@parametrize_typing_module('Literal')
def test_parse_type_hint_literal(m):
  assert parse_type_hint(m.Literal) == Unknown(m.Literal)
  assert parse_type_hint(m.Literal[4, '42']) == Literal(m.Literal[4, '42'], (4, '42'))


def test_parse_type_hint_new_type():
  assert parse_type_hint(t.NewType) == Unknown(t.NewType)
  new_type = t.NewType('MyInt', int)
  assert parse_type_hint(new_type) == NewType(new_type, 'MyInt', int)


def test_parse_type_hint_concrete_type():
  assert parse_type_hint(int) == Type(int, int, None)
  assert parse_type_hint(object) == Type(object, object, None)
  assert parse_type_hint(collections.abc.Iterable) == Type(collections.abc.Iterable, collections.abc.Iterable, None)


def test_parse_type_hint_special_generic_alias():
  assert parse_type_hint(t.List) == Type(t.List, list, None)  # _handle_special_generic_alias()
  assert parse_type_hint(t.List[int]) == Type(t.List[int], list, (int,))  # _handle_generic_alias()
  assert parse_type_hint(t.List[T]) == Type(t.List[T], list, (T,))  # _handle_generic_alias()


@pytest.mark.skipif(sys.version_info[:2] < (3, 10), reason='PEP 585 is implemented starting with Python 3.10')
def test_parse_type_hint_special_generic_alias_pep585():
  assert parse_type_hint(list) == Type(list, list, None)  # _handle_concrete_type()
  assert parse_type_hint(list[int]) == Type(list[int], list, (int,))  # _handle_generic_alias()
  assert parse_type_hint(list[T]) == Type(list[T], list, (T,))  # _handle_generic_alias()


def test_parse_type_hint_generic_alias_of_concrete_type():
  class MyGeneric(t.Generic[T]): pass
  assert parse_type_hint(MyGeneric) == Type(MyGeneric, MyGeneric, None)
  assert parse_type_hint(MyGeneric[int]) == Type(MyGeneric[int], MyGeneric, (int,))
  assert parse_type_hint(MyGeneric[T]) == Type(MyGeneric[T], MyGeneric, (T,))

  class MyList(t.List[T]): pass
  assert parse_type_hint(MyList) == Type(MyList, MyList, None)
  assert parse_type_hint(MyList[int]) == Type(MyList[int], MyList, (int,))
  assert parse_type_hint(MyList[T]) == Type(MyList[T], MyList, (T,))

  class MyConcreteList(t.List[int]): pass
  assert parse_type_hint(MyConcreteList) == Type(MyConcreteList, MyConcreteList, None)


def test_parse_type_hint_unknown():
  assert parse_type_hint(42) == Unknown(42)
