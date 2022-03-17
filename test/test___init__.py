
import sys
import typing
import pytest
import typeapi

from typeapi import Type


def test_typeapi_example():
  hint = typeapi.of(typing.List[int])
  assert hint == Type(list, nparams=1, parameters=None, args=(Type.of(int),))


@pytest.mark.skipif(sys.version_info[:2] < (3, 10), reason='PEP 585 is implemented starting with Python 3.10')
def test_typeapi_example_pep585():
  if sys.version_info[:2] >= (3, 10):  # So mypy doesn't complain
    hint = typeapi.of(int | str | None)
    assert hint == typeapi.Union((Type.of(int), Type.of(str), Type.of(type(None))))


def test_import_all():
  exec('from typeapi import *')
