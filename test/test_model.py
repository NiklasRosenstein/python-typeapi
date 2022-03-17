
import collections.abc
import sys
import typing as t
import pytest
import typeapi
from typeapi.model import ForwardRef, Type, Annotated, TypeVar, eval_types, infuse_type_parameters
from typeapi.utils import is_generic
from utils import parametrize_typing_module

T = t.TypeVar('T')
U = t.TypeVar('U')
K = t.TypeVar('K')
V = t.TypeVar('V')

class MyGeneric1(t.Generic[T]): pass
class MyGeneric2(MyGeneric1[int], t.Generic[T]): pass
class MyGeneric3(t.Generic[T], MyGeneric2[T]): pass
class MyGenericList(t.List[T]): pass
class MyConcreteList(t.List[int]): pass


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

  assert Type.of(MyGeneric1) == Type(MyGeneric1, 1, (T,), None)
  assert Type.of(MyGeneric1[int]) == Type(MyGeneric1, 1, (T,), (Type.of(int),))
  assert Type.of(MyGeneric1[T]) == Type(MyGeneric1, 1, (T,), (TypeVar(T),))

  assert Type.of(MyGenericList) == Type(MyGenericList, 1, (T,), None)
  assert Type.of(MyGenericList[int]) == Type(MyGenericList, 1, (T,), (Type.of(int),))
  assert Type.of(MyGenericList[T]) == Type(MyGenericList, 1, (T,), (TypeVar(T),))

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


def test_type_get_parameter_mapping():
  assert Type.of(int).get_parameter_mapping() == {}
  assert Type.of(t.List).get_parameter_mapping() == {}
  assert Type.of(t.List[int]).get_parameter_mapping() == {}
  assert Type.of(t.Dict[str, int]).get_parameter_mapping() == {}
  assert Type.of(t.Dict[str, int]).get_parameter_mapping() == {}

  assert Type.of(MyGeneric1).get_parameter_mapping() == {}
  assert Type.of(MyGeneric1[int]).get_parameter_mapping() == {T: Type.of(int)}

  # In MyGeneric2, the type variable T is specialized in one of the base classes, but also re-used
  # as a type variable in the body.
  assert Type.of(MyGeneric2).get_parameter_mapping() == {T: Type.of(int)}
  assert Type.of(MyGeneric2[str]).get_parameter_mapping() == {T: Type.of(str)}
  assert is_generic(MyGeneric2)
  assert Type.of(MyGeneric2.__orig_bases__[0]).get_parameter_mapping() == {T:Type.of(int)}


def test_type_get_orig_bases():
  assert list(Type.of(int).get_orig_bases()) == []
  assert list(Type.of(t.List[int]).get_orig_bases()) == []
  assert list(Type.of(t.Generic[T]).get_orig_bases()) == []

  assert list(Type.of(MyGeneric1).get_orig_bases()) == [t.Generic[T]]
  assert list(Type.of(MyGeneric1[int]).get_orig_bases()) == [t.Generic[T]]

  assert list(Type.of(MyGeneric2).get_orig_bases()) == [MyGeneric1[int], t.Generic[T]]

  assert list(Type.of(MyGeneric3).get_orig_bases()) == [t.Generic[T], MyGeneric2[T]]
  assert list(Type.of(MyGeneric3).get_orig_bases(True)) == [t.Generic[T], MyGeneric2[T], MyGeneric1[int]]


def test_base_type_parameters():
  # Test to ensure that even though the type variable T is re-used, it is actually assigned the type *int*
  # in the bases of MyGeneric2, which we must maintain when getting all the parametrized bases.
  assert Type.of(MyGeneric3[str]).get_orig_bases_parametrized(True) == {
    MyGeneric2[T]: Type.of(MyGeneric2[str]),
    MyGeneric1[int]: Type.of(MyGeneric1[int]),
  }

  class MyGeneric4(MyGeneric1[K], t.Generic[K, V]): pass
  class MyGeneric5(MyGeneric4[str, V]): pass

  # Test to ensure that the type variable mix-up as expected.
  assert Type.of(MyGeneric4[str, int]).get_orig_bases_parametrized(True) == {
    MyGeneric1[K]: Type.of(MyGeneric1[str]),
  }

  # Test to ensure that the type variable mix-up as expected.
  assert Type.of(MyGeneric5[int]).get_orig_bases_parametrized(True) == {
    MyGeneric4[str, V]: Type.of(MyGeneric4[str, int]),
    MyGeneric1[K]: Type.of(MyGeneric1[str]),
  }


def test_base_type_parameters_invalid_scenario_unbound_type_variable_1():
  # Test type-wise invalid scenario, but still possible to pull of at runtime.
  class A:
    a: T  # type: ignore[valid-type]  # Type variable "T" is unbound
  class B(A, t.Generic[T]):
    b: T
  assert list(Type.of(A).get_orig_bases(True)) == []
  assert list(Type.of(B).get_orig_bases(True)) == [t.Generic[T]]
  assert Type.of(B[int]).get_orig_bases_parametrized(True) == {}


def test_base_type_parameters_invalid_scenario_unbound_type_variable_2():
  # Test type-wise invalid scenario, but still possible to pull of at runtime.
  class A(t.Generic[K]):
    a: T  # type: ignore[valid-type]  # Type variable "T" is unbound
  class B(A, t.Generic[T]):
    b: T
  assert list(Type.of(A).get_orig_bases(True)) == [t.Generic[K]]
  assert list(Type.of(B).get_orig_bases(True)) == [t.Generic[T]]
  assert Type.of(B[int]).get_orig_bases_parametrized(True) == {}


def test_base_type_parameters_unparametrized_base_class():
  # Test what happens if we don't parametrize the base.
  class A(t.Generic[T]):
    a: T
  class B(A, t.Generic[T]):
    b: T
  assert list(Type.of(A).get_orig_bases(True)) == [t.Generic[T]]
  assert list(Type.of(B).get_orig_bases(True)) == [t.Generic[T]]
  assert Type.of(B[int]).get_orig_bases_parametrized(True) == {}

  # In contrast to
  class B2(A[str], t.Generic[T]):
    b: T
  assert list(Type.of(B2).get_orig_bases(True)) == [A[str], t.Generic[T]]
  assert Type.of(B2[int]).get_orig_bases_parametrized(True) == {A[str]: Type.of(A[str])}
  # In contrast to
  class B3(A[T], t.Generic[T]):
    b: T
  assert list(Type.of(B3).get_orig_bases(True)) == [A[T], t.Generic[T]]
  assert Type.of(B3[int]).get_orig_bases_parametrized(True) == {A[T]: Type.of(A[int])}


def test_ForwardRef_evaluate():
  ref = ForwardRef(t.ForwardRef('T'))
  assert ref.evaluate(__name__) is T
  with pytest.raises(RuntimeError):
    ref.evaluate()
  assert eval_types(ref, __name__) == TypeVar(T)

  if sys.version_info[:3] > (3, 9, 6):
    ref = ForwardRef(t.ForwardRef('T', module=__name__))  # type: ignore[call-arg]  # mypy doesn't seem to understand comparing version_info against a three-part version
    assert ref.evaluate() is T
    assert ref.evaluate('foobar32') is T


def test_eval_types():
  assert eval_types(typeapi.of(t.Dict['T', str]), __name__) == Type(dict, 2, None, (TypeVar(T), Type.of(str)))


def test_infuse_type_parameters():
  assert infuse_type_parameters(Type.of(t.List[T]), {t.cast(t.TypeVar, T): Type.of(int)}) == Type.of(t.List[int])
  assert infuse_type_parameters(Type.of(t.List[T]), {}) == Type.of(t.List[T ])

  class A(t.Generic[T]):
    a: T
  class B(A[U], t.Generic[U]):
    b: str
  type_parameters = Type.of(B[int]).get_parameter_mapping()
  assert type_parameters == {T: typeapi.of(U), U: Type.of(int)}
  assert infuse_type_parameters(Type.of(B), type_parameters) == Type.of(B)
  assert infuse_type_parameters(Type.of(A[T]), type_parameters) == Type.of(A[int])
