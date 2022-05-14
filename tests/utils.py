
import typing as t
import typing_extensions as te

import pytest

T = t.TypeVar('T')


def typing_modules_for_member(member_name: str) -> t.Sequence[t.Any]:
  assert hasattr(te, member_name), member_name
  if hasattr(t, member_name):
    return (t, te)
  return (te,)


def parametrize_typing_module(member_name: str, argname: str = 'm') -> t.Callable[[T], T]:
  def _decorator(func: T) -> T:
    return pytest.mark.parametrize(argname, typing_modules_for_member(member_name))(func)  # type: ignore
  return _decorator
