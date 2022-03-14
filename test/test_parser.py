
import collections.abc
import sys
import typing as t

import pytest
from typeapi.api import Annotated, Any, ClassVar, Final, ForwardRef, Literal, NewType, NoReturn, Type, TypeGuard, Union, Unknown
from typeapi.parser import parse_type_hint
from utils import parametrize_typing_module

T = t.TypeVar('T')


def test_parser_type_hint_any():
  assert parse_type_hint(t.Any) == Any()


@parametrize_typing_module('Annotated')
def test_parse_type_hint_annotated(m):
  assert parse_type_hint(m.Annotated[int, 42]) == Annotated(int, (42,))


def test_parse_type_hint_forward_ref():
  assert parse_type_hint('str') == ForwardRef('str', None)
  assert parse_type_hint(t.ForwardRef('str')) == ForwardRef('str', None)


def test_parse_type_hint_class_var():
  assert parse_type_hint(t.ClassVar) == Unknown(t.ClassVar)
  assert parse_type_hint(t.ClassVar[int]) == ClassVar(int)


@parametrize_typing_module('Final')
def test_parse_type_hint_final(m):
  assert parse_type_hint(m.Final) == Unknown(m.Final)
  assert parse_type_hint(m.Final[int]) == Final(int)


def test_parse_type_hint_no_return():
  assert parse_type_hint(t.NoReturn) == NoReturn()


@parametrize_typing_module('TypeGuard')
def test_parse_type_hint_type_guard(m):
  assert parse_type_hint(m.TypeGuard) == Unknown(m.TypeGuard)
  assert parse_type_hint(m.TypeGuard[str]) == TypeGuard(str)


def test_parse_type_hint_union():
  assert parse_type_hint(t.Union) == Unknown(t.Union)
  assert parse_type_hint(t.Union[int, str]) == Union((int, str))
  assert parse_type_hint(t.Optional[int]) == Union((int, type(None)))
  assert parse_type_hint(t.Union[int, None, str]) == Union((int, type(None), str))


@pytest.mark.skipif(sys.version_info[:2] < (3, 10), reason='PEP 585 is implemented starting with Python 3.10')
def test_parse_type_hint_union_pep585():
  assert parse_type_hint(int | str) == Union((int, str))
  assert parse_type_hint(int | None) == Union((int, type(None)))
  assert parse_type_hint(int | None | str) == Union((int, type(None), str))


@parametrize_typing_module('Literal')
def test_parse_type_hint_literal(m):
  assert parse_type_hint(m.Literal) == Unknown(m.Literal)
  assert parse_type_hint(m.Literal[4, '42']) == Literal((4, '42'))


def test_parse_type_hint_new_type():
  assert parse_type_hint(t.NewType) == Unknown(t.NewType)
  assert parse_type_hint(t.NewType('MyInt', int)) == NewType('MyInt', int)


def test_parse_type_hint_concrete_type():
  assert parse_type_hint(int) == Type(int, None)
  assert parse_type_hint(object) == Type(object, None)
  assert parse_type_hint(collections.abc.Iterable) == Type(collections.abc.Iterable, None)


def test_parse_type_hint_special_generic_alias():
  assert parse_type_hint(t.List) == Type(list, None)  # _handle_special_generic_alias()
  assert parse_type_hint(t.List[int]) == Type(list, (int,))  # _handle_generic_alias()
  assert parse_type_hint(t.List[T]) == Type(list, (T,))  # _handle_generic_alias()


@pytest.mark.skipif(sys.version_info[:2] < (3, 10), reason='PEP 585 is implemented starting with Python 3.10')
def test_parse_type_hint_special_generic_alias_pep585():
  assert parse_type_hint(list) == Type(list, None)  # _handle_concrete_type()
  assert parse_type_hint(list[int]) == Type(list, (int,))  # _handle_generic_alias()
  assert parse_type_hint(list[T]) == Type(list, (T,))  # _handle_generic_alias()


def test_parse_type_hint_generic_alias():
  class MyGeneric(t.Generic[T]): pass
  assert parse_type_hint(MyGeneric) == Type(MyGeneric, None)
  assert parse_type_hint(MyGeneric[int]) == Type(MyGeneric, (int,))
  assert parse_type_hint(MyGeneric[T]) == Type(MyGeneric, (T,))

  class MyList(t.List[T]): pass
  assert parse_type_hint(MyList) == Type(MyList, None)
  assert parse_type_hint(MyList[int]) == Type(MyList, (int,))
  assert parse_type_hint(MyList[T]) == Type(MyList, (T,))

  class MyConcreteList(t.List[int]): pass
  assert parse_type_hint(MyConcreteList) == Type(MyConcreteList, None)


def test_parse_type_hint_unknown():
  assert parse_type_hint(42) == Unknown(42)
