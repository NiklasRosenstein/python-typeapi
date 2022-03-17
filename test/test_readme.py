
import collections.abc
from typeapi import *
import typing_extensions as te


def test_readme_example():
  import typing, typeapi
  value = typeapi.of(typing.Mapping[te.Annotated[str, "key"], typing.Literal[True, None, 'false']])
  assert value == Type(collections.abc.Mapping, nparams=2, args=(Annotated(Type(str, nparams=0), ('key',)), Literal(values=(True, None, 'false'))))
