
import sys
import typing as t
import typing_extensions as te

import pytest
from typeapi.utils import get_special_forms, get_special_generic_aliases, is_annotated_alias, is_generic_alias, is_special_form, is_special_generic_alias

T = t.TypeVar('T')


def test_is_generic_alias():
  assert is_generic_alias(t.List[int])
  assert not is_generic_alias(t.List)
  assert not is_generic_alias(int)

  class MyGeneric(t.Generic[T]): pass
  assert is_generic_alias(MyGeneric[int])
  assert not is_generic_alias(MyGeneric)

  assert is_generic_alias(t.Tuple[int, str])
  assert is_generic_alias(t.Tuple[int, ...])
  assert is_generic_alias(te.Annotated[int, 42])

  assert not is_generic_alias(t.Optional[int])
  assert not is_generic_alias(t.Union[int, str])
  assert not is_generic_alias(t.Union[None, int])


@pytest.mark.skipif(sys.version_info[:2] < (3, 10), reason='PEP 585 is implemented starting with Python 3.10')
def test_is_generic_alias_pep585():
  assert is_generic_alias(list[str])
  assert is_generic_alias(dict[str, str])
  assert is_generic_alias(tuple[int, ...])
  assert is_generic_alias(tuple[str, int])

  assert not is_generic_alias(int | None)
  assert not is_generic_alias(int | str)
  assert not is_generic_alias(None | int)


def test_is_special_form():
  assert is_special_form(t.Any)
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


def test_is_annotated_alias():
  assert is_annotated_alias(te.Annotated[int, 42])
  assert not is_annotated_alias(int)
  assert not is_annotated_alias(42)


def test_get_special_generic_aliases():
  assert set(get_special_generic_aliases().keys()).issuperset(['List', 'Mapping', 'MutableMapping', 'Dict', 'Callable', 'Tuple'])


def test_get_special_forms():
  assert set(get_special_forms().keys()).issuperset(['Any', 'Union', 'NoReturn', 'ClassVar'])
