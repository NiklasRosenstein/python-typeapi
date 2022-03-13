
""" Parse #typing type hints. """

from __future__ import annotations
from pydoc import describe
import typing as t
from .utils import get_origins_to_special_generic_aliases, is_generic, is_generic_alias, is_special_generic_alias, TypeArg


class TypeInfo(t.NamedTuple):
  origin: t.Type
  nparams: int
  parameters: t.Optional[t.Tuple[t.TypeVar, ...]]
  args: t.Optional[t.Tuple[TypeArg, ...]]

  def with_args(self, args: t.Tuple[TypeArg, ...]) -> TypeInfo:
    return TypeInfo(self.origin, self.nparams, self.parameters, args)


def deconstruct_type(type_: t.Any) -> TypeInfo:

  def _raise() -> t.NoReturn: raise ValueError(f'unable to deconstruct {type_!r}')

  if is_special_generic_alias(type_):
    # Special generic aliases do no have explicit type variables associated in their definition.
    return TypeInfo(type_.__origin__, type_._nparams, None, None)

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
