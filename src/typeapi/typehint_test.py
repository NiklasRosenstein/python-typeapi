from typing import Any, List, TypeVar, Union

from typing_extensions import Annotated, Literal

from typeapi.typehint import AnnotatedTypeHint, ClassTypeHint, LiteralTypeHint, TypeHint, UnionTypeHint

T = TypeVar("T")


def test__TypeHint__any() -> None:
    assert TypeHint(Any) == ClassTypeHint(Any)
    assert TypeHint(Any).hint == Any
    assert TypeHint(Any).origin is None
    assert TypeHint(Any).args == ()
    assert TypeHint(Any).parameters == ()


def test__TypeHint__int() -> None:
    hint = TypeHint(int)
    assert isinstance(hint, ClassTypeHint)
    assert hint.hint == int
    assert hint.origin is None
    assert hint.args == ()
    assert hint.parameters == ()


def test__TypeHint__list_generic() -> None:
    hint = TypeHint(List)
    assert isinstance(hint, ClassTypeHint)
    assert hint.hint == List
    assert hint.origin is list
    assert hint.args == ()
    assert str(hint.parameters) == "(~T,)"


def test__TypeHint__list_templatized() -> None:
    hint = TypeHint(List[T])
    assert isinstance(hint, ClassTypeHint)
    assert hint.hint == List[T]
    assert hint.args == (T,)
    assert str(hint.parameters) == "(~T,)"


def test__TypeHint__list_specialized() -> None:
    hint = TypeHint(List[int])
    assert isinstance(hint, ClassTypeHint)
    assert hint.hint == List[int]
    assert hint.origin is list
    assert hint.args == (int,)
    assert hint.parameters == ()


def test__TypeHint__union() -> None:
    hint = TypeHint(Union[int, str])
    assert isinstance(hint, UnionTypeHint)
    assert hint.hint == Union[int, str]
    assert hint.origin is Union
    assert hint.args == (int, str)
    assert hint.parameters == ()


def test__TypeHint__literal() -> None:
    hint = TypeHint(Literal[42, "foo"])
    assert isinstance(hint, LiteralTypeHint)
    assert hint.hint == Literal[42, "foo"]
    assert hint.origin is Literal
    assert hint.args == (42, "foo")
    assert hint.parameters == ()


def test__TypeHint__annotated() -> None:
    hint = TypeHint(Annotated[int, 42, "foo"])
    assert isinstance(hint, AnnotatedTypeHint)
    assert hint.hint == Annotated[int, 42, "foo"]
    assert hint.origin is Annotated
    assert hint.args == (int, 42, "foo")
    assert hint.parameters == ()
