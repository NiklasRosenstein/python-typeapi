
import collections.abc
import sys
import typing as t
import pytest
from typeapi.model import ForwardRef, Type, Annotated, TypeVar
from typeapi.utils import is_generic
from utils import parametrize_typing_module

T = t.TypeVar('T')
K = t.TypeVar('K')
V = t.TypeVar('V')


def test_Type_str():
  assert str(Type.of(int)) == 'Type(int)'
  assert str(Type.of(t.Dict[T, int])) == 'Type(dict, nparams=2, args=(TypeVar(~T), Type(int)))'


def test_Annotated_str():
  assert str(Annotated(Type.of(int), (42,))) == 'Annotated(Type(int), (42,))'
  assert str(Annotated(Type.of(int), (42, "foobar"))) == "Annotated(Type(int), (42, 'foobar'))"


def test_Type_of_any():
  assert Type.of(t.Any) == Type(object, 0, None, None)


def test_Type_of_generic():
  assert Type.of(t.Generic) == Type(t.Generic, 0, None, None)  # type: ignore[arg-type]
  assert Type.of(t.Generic[T]) == Type(t.Generic, 0, None, (TypeVar(T),))  # type: ignore[arg-type]

  class MyGeneric(t.Generic[T]): pass
  assert Type.of(MyGeneric) == Type(MyGeneric, 1, (T,), None)
  assert Type.of(MyGeneric[int]) == Type(MyGeneric, 1, (T,), (Type.of(int),))
  assert Type.of(MyGeneric[T]) == Type(MyGeneric, 1, (T,), (TypeVar(T),))

  class MyList(t.List[T]): pass
  assert Type.of(MyList) == Type(MyList, 1, (T,), None)
  assert Type.of(MyList[int]) == Type(MyList, 1, (T,), (Type.of(int),))
  assert Type.of(MyList[T]) == Type(MyList, 1, (T,), (TypeVar(T),))

  class MyConcreteList(t.List[int]): pass
  assert Type.of(MyConcreteList) == Type(MyConcreteList, 0, (), None)


def test_Type_of_special_generic():
  assert Type.of(t.List) == Type(list, 1, None, None)
  assert Type.of(t.List[int]) == Type(list, 1, None, (Type.of(int),))
  assert Type.of(t.List[T]) == Type(list, 1, None, (TypeVar(T),))
  assert Type.of(t.Mapping[str, int]) == Type(collections.abc.Mapping, 2, None, (Type.of(str), Type.of(int),))
  assert Type.of(t.Mapping[K, V]) == Type(collections.abc.Mapping, 2, None, (TypeVar(K), TypeVar(V),))


@parametrize_typing_module('Annotated')
def test_Type_of_annotated_errors(m):
  with pytest.raises(ValueError) as excinfo:
    assert Type.of(m.Annotated[int, 42])
  assert str(excinfo.value) == 'unable to deconstruct {}'.format(m.Annotated[int, 42])


def test_Type_of_concrete_type():
  assert Type.of(int) == Type(int, 0, None, None)


def test_Type_get_type_parameter_mapping():
  assert Type.of(int).get_parameter_mapping() == {}
  assert Type.of(t.List).get_parameter_mapping() == {}
  assert Type.of(t.List[int]).get_parameter_mapping() == {}
  assert Type.of(t.Dict[str, int]).get_parameter_mapping() == {}
  assert Type.of(t.Dict[str, int]).get_parameter_mapping() == {}

  class MyGeneric(t.Generic[T]):
    a: T
  assert Type.of(MyGeneric).get_parameter_mapping() == {}
  assert Type.of(MyGeneric[int]).get_parameter_mapping() == {T: Type.of(int)}

  # This is kind of a weird constellation.
  class WeirdGeneric(MyGeneric[str], t.Generic[T]):
    b: T
  assert Type.of(WeirdGeneric).get_parameter_mapping() == {T: Type.of(str)}
  assert Type.of(WeirdGeneric[int]).get_parameter_mapping() == {T: Type.of(int)}
  assert is_generic(WeirdGeneric)
  assert Type.of(WeirdGeneric.__orig_bases__[0]).get_parameter_mapping() == {T:Type.of(str)}


def test_ForwardRef_evaluate():
  ref = ForwardRef(t.ForwardRef('T'))
  assert ref.evaluate(__name__) is T
  with pytest.raises(RuntimeError):
    ref.evaluate()

  if sys.version_info[:3] > (3, 9, 6):
    ref = ForwardRef(t.ForwardRef('T', module=__name__))  # type: ignore[call-arg]  # mypy doesn't seem to understand comparing version_info against a three-part version
    assert ref.evaluate() is T
    assert ref.evaluate('foobar32') is T
