
from __future__ import annotations
import functools
import types
import typing as t
import typing_extensions as te

TypeArg = t.Union[
  te.ParamSpec,
  t.TypeVar,
  t.Tuple[()],
  'types.EllipsisType',
  t.Type,
]


class _BaseGenericAlias(te.Protocol):
  _inst: bool
  _name: str
  __origin__: type


class Generic(te.Protocol):
  __orig_bases__: t.ClassVar[t.Tuple[t.Type, ...]]
  __parameters__: t.Tuple[t.TypeVar, ...]


class GenericAlias(_BaseGenericAlias, te.Protocol):
  __args__: t.Tuple[TypeArg, ...]


class SpecialGenericAlias(_BaseGenericAlias, te.Protocol):
  _nparams: int


class AnnotatedAlias(_BaseGenericAlias, te.Protocol):
  __metadata__: t.Tuple[t.Any, ...]


class SpecialForm(te.Protocol):
  pass


def is_generic(hint: t.Any) -> te.TypeGuard[t.Type[Generic]]:
  return isinstance(hint, type) and issubclass(hint, t.Generic)  # type: ignore


def is_generic_alias(hint: t.Any) -> te.TypeGuard[GenericAlias]:
  """ Returns `True` if *hint* is a #t._GenericAlias or #types.GenericAlias. """

  if type(hint) is t._GenericAlias:  # type: ignore
    return True

  _GenericAlias = getattr(types, 'GenericAlias', None)
  if _GenericAlias is not None and isinstance(hint, _GenericAlias):
    return True

  return False


def is_special_generic_alias(hint: t.Any) -> te.TypeGuard[SpecialGenericAlias]:
  """ Returns `True` if *hint* is a #._SpecialGenericAlias (like #t.List or #t.Mapping). """

  return isinstance(hint, t._SpecialGenericAlias)  # type: ignore


def is_special_form(hint: t.Any) -> te.TypeGuard[SpecialGenericAlias]:
  """ Returns `True` if *hint* is a #._SpecialForm (like #t.Final or #t.Union). """

  return isinstance(hint, t._SpecialForm)


def is_annotated_alias(hint: t.Any) -> te.TypeGuard[AnnotatedAlias]:
  """ Returns `True` if *hint* is a #._AnnotatedAlias (e.g. `typing.Annotated[int, 42]`). """

  return isinstance(hint, t._AnnotatedAlias)  # type: ignore


@functools.lru_cache()
def get_special_generic_aliases() -> t.Dict[str, SpecialGenericAlias]:
  """ Returns a dictionary that contains all special generic aliases (like #t.List and #t.Mapping)
  defined in the #typing module. """

  result = {}
  for key, value in vars(t).items():
    if is_special_generic_alias(value):
      result[key] = value
  return result


@functools.lru_cache()
def get_origins_to_special_generic_aliases() -> t.Dict[type, SpecialGenericAlias]:
  return {v.__origin__: v for v in get_special_generic_aliases().values()}


@functools.lru_cache()
def get_special_forms() -> t.Dict[str, SpecialGenericAlias]:
  """ Returns a dictionary that contains all special forms (like #t.Final and #t.Union)
  defined in the #typing module. """

  result = {}
  for key, value in vars(t).items():
    if is_special_form(value):
      result[key] = value
  return result
