
import collections.abc
import typing as t
import typing_extensions as te

import pytest
from typeapi.deconstruct import deconstruct_type, TypeInfo

T = t.TypeVar('T')
K = t.TypeVar('K')
V = t.TypeVar('V')


def test_deconstruct_any():
  assert deconstruct_type(t.Any) == TypeInfo(object, 0, None, None)


def test_deconstruct_generic():
  class MyGeneric(t.Generic[T]): pass
  assert deconstruct_type(MyGeneric) == TypeInfo(MyGeneric, 1, (T,), None)
  assert deconstruct_type(MyGeneric[int]) == TypeInfo(MyGeneric, 1, (T,), (int,))
  assert deconstruct_type(MyGeneric[T]) == TypeInfo(MyGeneric, 1, (T,), (T,))

  class MyList(t.List[T]): pass
  assert deconstruct_type(MyList) == TypeInfo(MyList, 1, (T,), None)
  assert deconstruct_type(MyList[int]) == TypeInfo(MyList, 1, (T,), (int,))
  assert deconstruct_type(MyList[T]) == TypeInfo(MyList, 1, (T,), (T,))

  class MyConcreteList(t.List[int]): pass
  assert deconstruct_type(MyConcreteList) == TypeInfo(MyConcreteList, 0, (), None)


def test_deconstruct_special_generic():
  assert deconstruct_type(t.List) == TypeInfo(list, 1, None, None)
  assert deconstruct_type(t.List[int]) == TypeInfo(list, 1, None, (int,))
  assert deconstruct_type(t.List[T]) == TypeInfo(list, 1, None, (T,))
  assert deconstruct_type(t.Mapping[str, int]) == TypeInfo(collections.abc.Mapping, 2, None, (str, int,))
  assert deconstruct_type(t.Mapping[K, V]) == TypeInfo(collections.abc.Mapping, 2, None, (K, V,))


def test_deconstruct_annotated_errors():
  with pytest.raises(ValueError) as excinfo:
    assert deconstruct_type(te.Annotated[int, 42])
  assert str(excinfo.value) == 'unable to deconstruct {}'.format(te.Annotated[int, 42])
