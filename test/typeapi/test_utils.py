
import typing as t
import typing_extensions as te
from typeapi.utils import get_special_forms, get_special_generic_aliases, is_generic_alias, is_special_form, is_special_generic_alias

T = t.TypeVar('T')


def test_is_generic_alias():
  assert is_generic_alias(t.List[int])
  assert not is_generic_alias(t.List)
  assert not is_generic_alias(int)

  class MyGeneric(t.Generic[T]): pass
  assert is_generic_alias(MyGeneric[int])
  assert not is_generic_alias(MyGeneric)

  assert not is_generic_alias(te.Annotated[int, 42])


def test_is_special_form():
  assert not is_special_form(t.Any)
  assert is_special_form(t.ClassVar)
  assert is_special_form(t.Union)
  assert not is_special_form(t.List)
  assert not is_special_form(int)
  assert not is_special_form(42)


def test_is_special_generic_alias():
  assert is_special_generic_alias(t.List)
  assert is_special_generic_alias(t.Mapping)
  assert is_special_generic_alias(t.Dict)
  assert is_special_generic_alias(t.Tuple)
  assert not is_special_generic_alias(t.List[int])
  assert not is_special_generic_alias(int)
  assert not is_special_generic_alias(42)


def test_get_special_generic_aliases():
  assert set(get_special_generic_aliases().keys()).issuperset(['List', 'Mapping', 'MutableMapping', 'Dict'])


def test_get_special_forms():
  assert set(get_special_forms().keys()).issuperset(['Union', 'NoReturn', 'ClassVar'])
