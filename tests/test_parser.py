import collections.abc
import sys
import typing as t

import pytest
from utils import parametrize_typing_module

from typeapi.model import (
    Annotated,
    Any,
    ClassVar,
    Final,
    ForwardRef,
    Literal,
    NewType,
    NoReturn,
    Type,
    TypeGuard,
    TypeVar,
    Union,
    Unknown,
)
from typeapi.parser import parse_type_hint
from typeapi.utils import is_new_type

T = t.TypeVar("T")


def test_parser_type_hint_any():
    assert parse_type_hint(t.Any) == Any()


@parametrize_typing_module("Annotated")
def test_parse_type_hint_annotated(m):
    assert parse_type_hint(m.Annotated[int, 42]) == Annotated(Type.of(int), (42,))


def test_parse_type_hint_forward_ref():
    assert parse_type_hint("str") == ForwardRef(t.ForwardRef("str"))
    assert parse_type_hint(t.ForwardRef("str")) == ForwardRef(t.ForwardRef("str"))


def test_parse_type_hint_class_var():
    assert parse_type_hint(t.ClassVar) == Unknown(t.ClassVar)
    assert parse_type_hint(t.ClassVar[int]) == ClassVar(Type.of(int))


@parametrize_typing_module("Final")
def test_parse_type_hint_final(m):
    assert parse_type_hint(m.Final) == Unknown(m.Final)
    assert parse_type_hint(m.Final[int]) == Final(Type.of(int))


def test_parse_type_hint_no_return():
    assert parse_type_hint(t.NoReturn) == NoReturn()


@parametrize_typing_module("TypeGuard")
def test_parse_type_hint_type_guard(m):
    assert parse_type_hint(m.TypeGuard) == Unknown(m.TypeGuard)
    assert parse_type_hint(m.TypeGuard[str]) == TypeGuard(Type.of(str))


def test_parse_type_hint_union():
    assert parse_type_hint(t.Union) == Unknown(t.Union)
    assert parse_type_hint(t.Union[int, str]) == Union((Type.of(int), Type.of(str)))
    assert parse_type_hint(t.Optional[int]) == Union((Type.of(int), Type.of(type(None))))
    assert parse_type_hint(t.Union[int, None, str]) == Union((Type.of(int), Type.of(type(None)), Type.of(str)))


@pytest.mark.skipif(sys.version_info[:2] < (3, 10), reason="PEP 585 is implemented starting with Python 3.10")
def test_parse_type_hint_union_pep585():
    if sys.version_info[:2] >= (3, 10):  # So mypy doesn't complain
        assert parse_type_hint(int | str) == Union((Type.of(int), Type.of(str)))
        assert parse_type_hint(int | None) == Union((Type.of(int), Type.of(type(None))))
        assert parse_type_hint(int | None | str) == Union((Type.of(int), Type.of(type(None)), Type.of(str)))


@parametrize_typing_module("Literal")
def test_parse_type_hint_literal(m):
    assert parse_type_hint(m.Literal) == Unknown(m.Literal)
    assert parse_type_hint(m.Literal[4, "42"]) == Literal((4, "42"))


def test_parse_type_hint_new_type():
    assert parse_type_hint(t.NewType) == Unknown(t.NewType)
    MyInt = t.NewType("MyInt", int)
    assert is_new_type(MyInt)
    assert parse_type_hint(MyInt) == NewType(MyInt)


def test_parse_type_hint_concrete_type():
    assert parse_type_hint(int) == Type.of(int)
    assert parse_type_hint(object) == Type.of(object)
    assert parse_type_hint(collections.abc.Iterable) == Type.of(collections.abc.Iterable)


def test_parse_type_hint_special_generic_alias():
    assert parse_type_hint(t.List) == Type.of(t.List)
    assert parse_type_hint(t.List[int]) == Type.of(t.List[int])
    assert parse_type_hint(t.List[T]) == Type.of(t.List[T])


@pytest.mark.skipif(sys.version_info[:2] < (3, 10), reason="PEP 585 is implemented starting with Python 3.10")
def test_parse_type_hint_special_generic_alias_pep585():
    if sys.version_info[:2] >= (3, 10):  # So mypy doesn't complain
        assert parse_type_hint(list) == Type.of(list)
        assert parse_type_hint(list[int]) == Type.of(list[int])
        assert parse_type_hint(list[T]) == Type.of(list[T])


def test_parse_type_hint_generic_alias_of_concrete_type():
    class MyGeneric(t.Generic[T]):
        pass

    assert parse_type_hint(MyGeneric) == Type.of(MyGeneric)
    assert parse_type_hint(MyGeneric[int]) == Type.of(MyGeneric[int])
    assert parse_type_hint(MyGeneric[T]) == Type.of(MyGeneric[T])

    class MyList(t.List[T]):
        pass

    assert parse_type_hint(MyList) == Type.of(MyList)
    assert parse_type_hint(MyList[int]) == Type.of(MyList[int])
    assert parse_type_hint(MyList[T]) == Type.of(MyList[T])

    class MyConcreteList(t.List[int]):
        pass

    assert parse_type_hint(MyConcreteList) == Type.of(MyConcreteList)


def test_parse_type_hint_type_var():
    assert parse_type_hint(T) == TypeVar(T)


def test_parse_type_hint_unknown():
    assert parse_type_hint(42) == Unknown(42)
