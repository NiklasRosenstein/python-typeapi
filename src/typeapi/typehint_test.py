from typing import Any, Generic, List, TypeVar, Union

from typing_extensions import Annotated, Literal

from typeapi.typehint import (
    AnnotatedTypeHint,
    ClassTypeHint,
    ForwardRefTypeHint,
    LiteralTypeHint,
    TypeHint,
    TypeVarTypeHint,
    UnionTypeHint,
)
from typeapi.utils import ForwardRef

T = TypeVar("T")
U = TypeVar("U")


def test__TypeHint__any() -> None:
    hint = TypeHint(Any)
    assert isinstance(hint, ClassTypeHint)
    assert hint.hint == Any
    assert hint.origin is object
    assert hint.type is object
    assert hint.args == ()
    assert hint.parameters == ()
    assert len(hint) == 0


def test__TypeHint__int() -> None:
    hint = TypeHint(int)
    assert isinstance(hint, ClassTypeHint)
    assert hint.hint == int
    assert hint.origin is None
    assert hint.type is int
    assert hint.args == ()
    assert hint.parameters == ()
    assert len(hint) == 0


def test__TypeHint__list_generic() -> None:
    hint = TypeHint(List)
    assert isinstance(hint, ClassTypeHint)
    assert hint.hint == List
    assert hint.origin is list
    assert hint.type is list
    assert hint.args == ()
    assert str(hint.parameters) == "(~T,)"
    assert len(hint) == 0


def test__TypeHint__list_templatized() -> None:
    hint = TypeHint(List[T])
    assert isinstance(hint, ClassTypeHint)
    assert hint.hint == List[T]
    assert hint.origin is list
    assert hint.type is list
    assert hint.args == (T,)
    assert str(hint.parameters) == "(~T,)"
    assert len(hint) == 1


def test__TypeHint__list_specialized() -> None:
    hint = TypeHint(List[int])
    assert isinstance(hint, ClassTypeHint)
    assert hint.hint == List[int]
    assert hint.origin is list
    assert hint.type is list
    assert hint.args == (int,)
    assert hint.parameters == ()
    assert len(hint) == 1

    hint_0 = hint[0]
    assert isinstance(hint_0, ClassTypeHint)
    assert hint_0.type == int


def test__TypeHint__union() -> None:
    hint = TypeHint(Union[int, str])
    assert isinstance(hint, UnionTypeHint)
    assert hint.hint == Union[int, str]
    assert hint.origin is Union
    assert hint.args == (int, str)
    assert hint.parameters == ()
    assert len(hint) == 2

    hint_0 = hint[0]
    assert isinstance(hint_0, ClassTypeHint)
    assert hint_0.type == int

    hint_1 = hint[1]
    assert isinstance(hint_1, ClassTypeHint)
    assert hint_1.type == str


def test__TypeHint__literal() -> None:
    hint = TypeHint(Literal[42, "foo"])
    assert isinstance(hint, LiteralTypeHint)
    assert hint.hint == Literal[42, "foo"]
    assert hint.origin is Literal
    assert hint.args == ()
    assert hint.parameters == ()
    assert hint.values == (42, "foo")
    assert len(hint) == 0


def test__TypeHint__annotated() -> None:
    hint = TypeHint(Annotated[int, 42, "foo"])
    assert isinstance(hint, AnnotatedTypeHint)
    assert hint.hint == Annotated[int, 42, "foo"]
    assert hint.origin is Annotated
    assert hint.args == (int,)
    assert hint.parameters == ()
    assert hint.metadata == (42, "foo")
    assert len(hint) == 1

    hint_0 = hint[0]
    assert isinstance(hint_0, ClassTypeHint)
    assert hint_0.type == int


def test__TypeHint__custom_generic_class() -> None:
    class MyGeneric(Generic[T, U]):
        pass

    hint = TypeHint(MyGeneric)
    assert isinstance(hint, ClassTypeHint)
    assert hint.hint == MyGeneric
    assert hint.origin is None
    assert hint.args == ()
    assert hint.parameters == (T, U)
    assert len(hint) == 0

    hint = TypeHint(MyGeneric[int, str])
    assert isinstance(hint, ClassTypeHint)
    assert hint.hint == MyGeneric[int, str]
    assert hint.origin is MyGeneric
    assert hint.args == (int, str)
    assert hint.parameters == ()
    assert len(hint) == 2

    hint = TypeHint(MyGeneric[int, T])
    assert isinstance(hint, ClassTypeHint)
    assert hint.hint == MyGeneric[int, T]
    assert hint.origin is MyGeneric
    assert hint.args == (int, T)
    assert hint.parameters == (T,)
    assert len(hint) == 2

    hint_0 = hint[0]
    assert isinstance(hint_0, ClassTypeHint)
    assert hint_0.type is int

    hint_1 = hint[1]
    assert isinstance(hint_1, TypeVarTypeHint)
    assert str(hint_1.hint) == "~T"


def test__TypeHint__from_TypeVar() -> None:
    hint = TypeHint(T)
    assert isinstance(hint, TypeVarTypeHint)
    assert hint.hint == T
    assert hint.origin is None
    assert hint.args == ()
    assert hint.parameters == ()
    assert hint.name == "T"
    assert not hint.covariant
    assert not hint.contravariant
    assert hint.bound is None
    assert hint.constraints == ()


def test__TypeHint__from_ForwardRef_string() -> None:
    hint = TypeHint("int")
    assert isinstance(hint, ForwardRefTypeHint)
    assert hint.hint == "int"
    assert hint.origin is None
    assert hint.args == ()
    assert hint.parameters == ()
    assert hint.ref == ForwardRef("int")


def test__TypeHint__from_ForwardRef_instance() -> None:
    hint = TypeHint(ForwardRef("int"))
    assert isinstance(hint, ForwardRefTypeHint)
    assert hint.hint == ForwardRef("int")
    assert hint.origin is None
    assert hint.args == ()
    assert hint.parameters == ()
    assert hint.ref == ForwardRef("int")
