
from __future__ import annotations
import dataclasses
import sys
import typing as t
from . import utils


class Hint:
  """ Base for classes that represent type hints. """

  def __init__(self) -> None:
    if type(self) is Hint:
      raise TypeError('Hint cannot be constructed')


@dataclasses.dataclass
class Type(Hint):
  """ Represents a concrete type, including type arguments if applicable. """

  #: The original Python type underlying the type hint.
  type: t.Type

  #: The number of type parameters that the #origin type accepts.
  nparams: int

  #: The type variables from the #origin type's original definition. Note that this may be `None`
  #: even if #nparams is greater than zero. This is usually the case for special generic aliases
  #: like #typing.List for which no explicit type variables are defined in the #typing module.
  parameters: t.Optional[t.Tuple[t.TypeVar, ...]]

  #: The type arguments that the #origin was parametrized with. This is #None if the type is not
  #: explicitly parametrized. It may still contain #typing.TypeVar#s if that is what the type was
  #: parametrized with.
  args: t.Optional[t.Tuple[utils.TypeArg, ...]]

  def __repr__(self) -> str:
    parts = [utils.type_repr(self.type), f'nparams={self.nparams}']
    if self.parameters is not None:
      parts.append(f'parameters={self.parameters!r}')
    if self.args is not None:
      parts.append(f'args=({", ".join(map(utils.type_repr, self.args))})')
    return f'Type({", ".join(parts)})'

  def with_args(self, args: t.Tuple[utils.TypeArg, ...]) -> Type:
    """ Return a copy of the #Type object, but #args replaced by the *args* parameter value. """

    return Type(self.type, self.nparams, self.parameters, args)

  @staticmethod
  def of(type_: t.Any) -> Type:
    """ Deconstruct a type hint that is concrete type or generic alias, i.e. one that is not a "special form" like
    #typing.Union or #typing.Any. Examples of types being accepted are any actual Python types, #typing.Any, special
    generic aliases like #typing.List (unspecialized) or generic aliases (like `typing.List[int]` or a parametrization
    of a #typing.Generic subclass).

    Arguments:
      type_ (any): The type hint to deconstruct.
    Raises:
      ValueError: If the *type_* parameter cannot be deconstructed into a #Type. For example,
        passing a #typing.Annotated object or #typing.ClassVar will cause this error to be raised.
    """

    def _raise() -> t.NoReturn: raise ValueError(f'unable to deconstruct {type_!r}')

    if type_ is t.Any:
      return Type(object, 0, None, None)

    if utils.is_special_generic_alias(type_):
      if sys.version_info[:2] <= (3, 8):
        nparams = len(type_.__parameters__)
      else:
        nparams = type_._nparams
      # Special generic aliases do no have explicit type variables associated in their definition.
      return Type(type_.__origin__, nparams, None, None)

    if utils.is_generic_alias(type_):
      # If the alias' origin points to a type that can only be represented by a special form from
      # the typing module, we want to deconstruct that type alias first.
      special_alias = utils.get_origins_to_special_generic_aliases().get(type_.__origin__)
      if special_alias is not None:
        type_info = Type.of(special_alias)

      # Otherwise, the alias origin must be a subclass of typing.Generic.
      elif utils.is_generic(type_.__origin__):
        type_info = Type.of(type_.__origin__)

      else:
        _raise()

      return type_info.with_args(type_.__args__)

    if utils.is_generic(type_):
      return Type(type_, len(type_.__parameters__), type_.__parameters__, None)

    # NOTE: It is important to run the isinstance() check here after testing for is_generic_alias(), because
    # starting with Python 3.10, instances of #types.GenericAlias test positive for isinstance(..., type).
    if isinstance(type_, type) and type_.__module__ not in ('typing', 'typing_extensions'):
      # NOTE: We don't want for example #typing.NewType (the class, not an instance of it) to be treated as a type.
      # With this block, we prevent types of the #typing module to be themselves represented as a #Type by typeapi.
      return Type(type_, 0, None, None)

    _raise()


@dataclasses.dataclass
class Union(Hint):
  """ Represents #typing.Union or #typing.Optional. """

  #: The types in this union.
  types: t.Tuple[utils.TypeArg, ...]


@dataclasses.dataclass
class Annotated(Hint):
  """ Represents a type wrapped in #typing.Annotated. """

  #: The type that is annotated.
  wrapped: utils.TypeArg

  #: The metadata in the annotation.
  metadata: t.Tuple[t.Any, ...]

  def __repr__(self) -> str:
    return 'Annotated({}, {})'.format(utils.type_repr(self.wrapped), ', '.join(map(repr, self.metadata)))


@dataclasses.dataclass
class ForwardRef(Hint):
  """ Represents a forward reference. """

  #: The expression of the forward reference.
  expr: str

  #: The module that is associated with the forward reference.
  module: t.Optional[str]

  def evaluate(self, fallback_module: t.Optional[str]) -> t.Any:
    raise NotImplementedError


@dataclasses.dataclass
class Any(Hint):  # type: ignore[misc]
  """ Represents #typing.Any. """


@dataclasses.dataclass
class ClassVar(Hint):
  """ Represents #typing.ClassVar. """

  #: The inner type.
  wrapped: utils.TypeArg


@dataclasses.dataclass
class Final(Hint):
  """ Represents #typing.Final. """

  #: The inner type.
  wrapped: utils.TypeArg


@dataclasses.dataclass
class NoReturn(Hint):
  """ Represents #typing.NoReturn. """


@dataclasses.dataclass
class TypeGuard(Hint):
  """ Represents #typing.TypeGuard. """

  #: The wrapped type.
  wrapped: utils.TypeArg


@dataclasses.dataclass
class Literal(Hint):
  """ Represents #typing.Literal. """

  #: The possible values represented by the literal.
  values: t.Tuple[t.Any, ...]


@dataclasses.dataclass
class NewType(Hint):
  """ Represents #typing.NewType. """

  #: The name of the new type.
  name: str

  #: The underlying type for the new type.
  supertype: t.Type


@dataclasses.dataclass
class Unknown(Hint):
  """ Represents an type hint that is not understood. """

  #: The type hint that could not be converted into the typeapi.
  hint: t.Any
