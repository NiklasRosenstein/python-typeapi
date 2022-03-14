
import typing as t
from typeapi.api import Type, Annotated

T = t.TypeVar('T')


def test_Type_str():
  assert str(Type(int, None)) == 'Type(int)'
  assert str(Type(dict, (T, int))) == 'Type(dict, (~T, int))'


def test_Annotated_str():
  assert str(Annotated(int, (42,))) == 'Annotated(int, 42)'
  assert str(Annotated(int, (42, "foobar"))) == "Annotated(int, 42, 'foobar')"
