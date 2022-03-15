
import typing as t
import typing_extensions as te
from typeapi.api import Type, Annotated

T = t.TypeVar('T')


def test_Type_str():
  assert str(Type(int, int)) == 'Type(int)'
  assert str(Type(t.Dict[T, int], dict)) == 'Type(dict, (~T, int))'


def test_Annotated_str():
  assert str(Annotated(te.Annotated[int, 42], int, (42,))) == 'Annotated(int, 42)'
  assert str(Annotated(te.Annotated[int, 42, "foobar"], int, (42, "foobar"))) == "Annotated(int, 42, 'foobar')"
