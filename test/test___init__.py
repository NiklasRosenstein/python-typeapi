
import sys
import typing
import pytest
import typeapi


def test_typeapi_example():
  hint = typeapi.of(typing.List[int])
  assert hint == typeapi.Type(list, nparams=1, parameters=None, args=(int,))


@pytest.mark.skipif(sys.version_info[:2] < (3, 10), reason='PEP 585 is implemented starting with Python 3.10')
def test_typeapi_example_pep585():
  hint = typeapi.of(int | str | None)
  assert hint == typeapi.Union((int, str, type(None)))


def test_import_all():
  exec('from typeapi import *')
