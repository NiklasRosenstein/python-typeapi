
""" Provides utilities to introspect #typing type hints. The goal is to assign the same semantics
to all viable members of the #typing module independent of the Python version. """

from __future__ import annotations
import functools
import sys
import types
import typing as t
import typing_extensions as te

if t.TYPE_CHECKING:
  import builtins

TypeArg = t.Union[
  te.ParamSpec,
  t.TypeVar,
  t.Tuple[()],
  'builtins.ellipsis',
  t.Type,
]


class _BaseGenericAlias(te.Protocol):
  _inst: bool
  _name: str
  __origin__: type
  __args__: t.Tuple[TypeArg, ...]


class Generic(te.Protocol):
  __orig_bases__: t.ClassVar[t.Tuple[t.Type, ...]]
  __parameters__: t.ClassVar[t.Tuple[t.TypeVar, ...]]


class GenericAlias(_BaseGenericAlias, te.Protocol):
  __parameters__: t.Tuple[t.TypeVar, ...]

  if sys.version_info[:2] <= (3, 8):
    _special: te.Literal[False]


if sys.version_info[:2] <= (3, 8):
  class SpecialGenericAlias(_BaseGenericAlias, te.Protocol):
    __parameters__: t.Tuple[t.TypeVar, ...]
    __args__: t.Tuple[TypeArg, ...]
    _special: te.Literal[True]
else:
  class SpecialGenericAlias(_BaseGenericAlias, te.Protocol):
    _nparams: int


if sys.version_info[:2] <= (3, 9):
  class UnionType(te.Protocol):
    __args__: t.Tuple[TypeArg, ...]
    __parameters__: t.Tuple[t.TypeVar, ...]
else:
  UnionType = types.UnionType


class AnnotatedAlias(_BaseGenericAlias, te.Protocol):
  __metadata__: t.Tuple[t.Any, ...]


class SpecialForm(te.Protocol):
  pass


class NewType(te.Protocol):
  __name__: str
  __supertype__: t.Type


def is_generic(hint: t.Any) -> te.TypeGuard[t.Type[Generic]]:
  """
  Returns:
    `True` if *hint* is a subclass fo #typing.Generic (and not an alias of it).
  """
  return isinstance(hint, type) and issubclass(hint, t.Generic)  # type: ignore[arg-type]


def is_generic_alias(hint: t.Any) -> te.TypeGuard[GenericAlias]:
  """
  Returns:
    `True` if *hint* is a #typing._GenericAlias or #types.GenericAlias ([PEP 585][] since Python 3.10+).

  [PEP 585]: https://peps.python.org/pep-0585/

  !!! note

      In Python versions 3.8 and older, #typing._GenericAlias is used also for special generic
      aliases (see #is_special_generic_alias()). This function will return `False` for these
      types of aliases to clearly distinct between special aliases and normal aliases, even if
      they share the same type.
  """

  if isinstance(hint, t._GenericAlias):  # type: ignore[attr-defined]
    if hint.__origin__ == t.Union:
      return False
    if sys.version_info[:2] <= (3, 8):
      return not hint._special
    return True  # type: ignore[unreachable]

  _GenericAlias = getattr(types, 'GenericAlias', None)
  if _GenericAlias is not None and isinstance(hint, _GenericAlias) and hint.__origin__ != t.Union:
    return True

  return False


def is_union_type(hint: t.Any) -> te.TypeGuard[UnionType]:
  """
  Returns:
    `True` if *hint* is a #typing.Union or #types.UnionType.
  """

  if isinstance(hint, t._GenericAlias) and hint.__origin__ == t.Union:  # type: ignore[attr-defined]
    return True

  if sys.version_info[:2] >= (3, 10):
    return isinstance(hint, types.UnionType)

  return False  # type: ignore[unreachable]


def is_special_generic_alias(hint: t.Any) -> te.TypeGuard[SpecialGenericAlias]:
  """
  Returns:
    `True` if *hint* is a #typing._SpecialGenericAlias (like #typing.List or #typing.Mapping).

  !!! note

      For Python versions 3.8 and older, the function treats #typing._GenericAliases
      as special if their `_special` attribute is set to `True`. #typing._SpecialGenericAlias
      was introduced in Python 3.9.
  """

  if sys.version_info[:2] <= (3, 8):
    # We use isinstance() here instead of checking the exact type because typing.Tuple or
    # typing.Callable in 3.8 or earlier are instances of typing._VariadicGenericAliases.
    if isinstance(hint, t._GenericAlias):  # type: ignore[attr-defined]
      return hint._special
    return False
  else:
    return isinstance(hint, t._SpecialGenericAlias)  # type: ignore[attr-defined]


def is_special_form(hint: t.Any) -> te.TypeGuard[SpecialGenericAlias]:
  """
  Returns:
    `True` if *hint* is a #typing._SpecialForm (like #typing.Final or #typing.Union).
  """

  return isinstance(hint, t._SpecialForm)


def is_annotated_alias(hint: t.Any) -> te.TypeGuard[AnnotatedAlias]:
  """
  Returns:
    `True` if *hint* is a #typing._AnnotatedAlias (e.g. `typing.Annotated[int, 42]`).
  """

  return isinstance(hint, te._AnnotatedAlias)  # type: ignore[attr-defined]


def is_new_type(hint: t.Any) -> te.TypeGuard[NewType]:
  """
  Returns:
    `True` if *hint* is a #typing.NewType object.
  """

  if sys.version_info[:2] <= (3, 9):
    return isinstance(hint, types.FunctionType) and hasattr(hint, '__supertype__')
  else:
    return isinstance(hint, t.NewType)  # type: ignore[arg-type]


@functools.lru_cache()
def get_special_generic_aliases() -> t.Dict[str, SpecialGenericAlias]:
  """ Returns a dictionary that contains all special generic aliases (like #typing.List and #typing.Mapping)
  defined in the #typing module.

  Example:

  ```py
  import typing
  from typeapi.utils import get_special_generic_aliases
  mapping = get_special_generic_aliases()
  assert mapping['List'] is typing.List
  ```"""

  result = {}
  for key, value in vars(t).items():
    if is_special_generic_alias(value):
      result[key] = value
  return result


@functools.lru_cache()
def get_origins_to_special_generic_aliases() -> t.Dict[type, SpecialGenericAlias]:
  """ Returns a dictionary that maps a native Python type to the #typing special generic alias.

  Example:

  ```py
  import typing
  from typeapi.utils import get_origins_to_special_generic_aliases
  mapping = get_origins_to_special_generic_aliases()
  assert mapping[list] is typing.List
  ```
  """

  return {v.__origin__: v for v in get_special_generic_aliases().values()}


@functools.lru_cache()
def get_special_forms() -> t.Dict[str, SpecialGenericAlias]:
  """ Returns a dictionary that contains all special forms (like #typing.Final and #typing.Union)
  defined in the #typing module.

  Example:

  ```py
  import typing
  from typeapi.utils import get_special_forms
  mapping = get_special_forms()
  assert mapping['Any'] is typing.Any
  assert mapping['Union'] is typing.Union
  ```
  """

  result = {}
  for key, value in vars(t).items():
    if is_special_form(value):
      result[key] = value
  return result


def type_repr(obj):
  """ #typing._type_repr() stolen from Python 3.8. """

  if isinstance(obj, type):
    if obj.__module__ == 'builtins':
      return obj.__qualname__
    return f'{obj.__module__}.{obj.__qualname__}'
  if obj is ...:
    return('...')
  if isinstance(obj, types.FunctionType):
    return obj.__name__
  return repr(obj)


def get_type_hints(type_: t.Any) -> t.Dict[str, t.Any]:
  """ Like #typing.get_type_hints(), but always includes extras. This is important when we want to inspect
  #typing.Annotated hints (without extras the annotations are removed). """

  if sys.version_info[:2] <= (3, 8):
    return t.get_type_hints(type_)
  else:
    return t.get_type_hints(type_, include_extras=True)
