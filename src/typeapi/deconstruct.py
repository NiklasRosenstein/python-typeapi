
""" Deconstruct concrete types and aliases. """

from __future__ import annotations
from pydoc import describe
import sys
import typing as t
from .utils import get_origins_to_special_generic_aliases, is_generic, is_generic_alias, is_special_generic_alias, TypeArg


class TypeInfo(t.NamedTuple):
  """ Contains information about a type hint that is either a fixed type or an alias (i.e. a parametrized type). """

  #: The original Python type underlying the type hint.
  origin: t.Type

  #: The number of type parameters that the #origin type accepts.
  nparams: int

  #: The type variables from the #origin type's original definition. Note that this may be `None`
  #: even if #nparams is greater than zero. This is usually the case for special generic aliases
  #: like #typing.List for which no explicit type variables are defined in the #typing module.
  parameters: t.Optional[t.Tuple[t.TypeVar, ...]]

  #: The type arguments that the #origin was parametrized with. This is #None if the type is not
  #: explicitly parametrized. It may still contain #typing.TypeVar#s if that is what the type was
  #: parametrized with.
  args: t.Optional[t.Tuple[TypeArg, ...]]

  def with_args(self, args: t.Tuple[TypeArg, ...]) -> TypeInfo:
    """ Return a copy of the #TypeInfo object, but #args replaced by the *args* parameter value. """

    return TypeInfo(self.origin, self.nparams, self.parameters, args)


def deconstruct_type(type_: t.Any) -> TypeInfo:
  """ Deconstruct a type hint that is not a #typing "special form" or another type of exotic hint,
  i.e. a hint that an actual singular type, and return its #TypeInfo.

  Arguments:
    type_ (any): The type hint to deconstruct.
  Raises:
    ValueError: If the *type_* parameter cannot be deconstructed into a #TypeInfo. For example,
      passing a #typing.Annotated object or #typing.ClassVar will cause this error to be raised.

  Example:

  ```py
  import collections.abc
  import typing
  from typeapi.deconstruct import deconstruct_type, TypeInfo
  T = typing.TypeVar('T')

  assert deconstruct_type(typing.Any) == TypeInfo(object, 0, None, None)
  assert deconstruct_type(typing.List) == TypeInfo(list, 1, None, None)
  assert deconstruct_type(t.Mapping[str, int]) == TypeInfo(collections.abc.Mapping, 2, None, (str, int,))

  class MyGeneric(t.Generic[T]): pass
  assert deconstruct_type(MyGeneric) == TypeInfo(MyGeneric, 1, (T,), None)
  assert deconstruct_type(MyGeneric[int]) == TypeInfo(MyGeneric, 1, (T,), (int,))
  assert deconstruct_type(MyGeneric[T]) == TypeInfo(MyGeneric, 1, (T,), (T,))
  ```
  """

  def _raise() -> t.NoReturn: raise ValueError(f'unable to deconstruct {type_!r}')

  if type_ is t.Any:
    return TypeInfo(object, 0, None, None)

  if is_special_generic_alias(type_):
    if sys.version_info[:2] <= (3, 8):
      nparams = len(type_.__parameters__)
    else:
      nparams = type_._nparams
    # Special generic aliases do no have explicit type variables associated in their definition.
    return TypeInfo(type_.__origin__, nparams, None, None)

  if is_generic_alias(type_):
    # If the alias' origin points to a type that can only be represented by a special form from
    # the typing module, we want to deconstruct that type alias first.
    special_alias = get_origins_to_special_generic_aliases().get(type_.__origin__)
    if special_alias is not None:
      type_info = deconstruct_type(special_alias)

    # Otherwise, the alias origin must be a subclass of typing.Generic.
    elif is_generic(type_.__origin__):
      type_info = deconstruct_type(type_.__origin__)

    else:
      _raise()

    return type_info.with_args(type_.__args__)

  if is_generic(type_):
    return TypeInfo(type_, len(type_.__parameters__), type_.__parameters__, None)

  _raise()
