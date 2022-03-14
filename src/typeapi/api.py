
import enum
import typing as t
from .deconstruct import TypeInfo
from .utils import TypeArg, type_repr


class Hint(t.NamedTuple):
  """ Base for classes that represent type hints. """


class Type(Hint, t.NamedTuple):
  """ Represents a concrete type, including type arguments if applicable. """

  #: The native Python type. Note that this may be #types.NoneType if the type hint
  #: represented is `None`.
  type: t.Type

  #: The type arguments, if applicable. This may yet contain type variables if that
  #: is what the original generic alias was created with.
  args: t.Optional[t.Tuple[t.Union[Hint, t.TypeVar], ...]]

  def __repr__(self) -> str:
    if self.args is None:
      return '{}({})'.format(self.__class__.__name__, type_repr(self.type))
    return '{}({}, ({}))'.format(self.__class__.__name__, type_repr(self.type), ', '.join(map(type_repr, self.args)))


class Union(Hint, t.NamedTuple):
  """ Represents #typing.Union or #typing.Optional. """

  #: The types in this union.
  types: t.Tuple[TypeArg, ...]


class Annotated(Hint, t.NamedTuple):
  """ Represents a type wrapped in #typing.Annotated. """

  #: The type that is annotated.
  wrapped: TypeArg

  #: The metadata in the annotation.
  metadata: t.Tuple[t.Any, ...]

  def __repr__(self) -> str:
    return 'Annotated({}, {})'.format(type_repr(self.wrapped), ', '.join(map(repr, self.metadata)))


class ForwardRef(Hint, t.NamedTuple):
  """ Represents a forward reference. """

  #: The expression of the forward reference.
  expr: str

  #: The module that is associated with the forward reference.
  module: t.Optional[str]

  def evaluate(self, fallback_module: t.Optional[str]) -> t.Any:
    raise NotImplementedError


class Any(Hint, t.NamedTuple):
  """ Represents #typing.Any. """


class ClassVar(Hint, t.NamedTuple):
  """ Represents #typing.ClassVar. """

  #: The inner type.
  wrapped: TypeArg


class Final(Hint, t.NamedTuple):
  """ Represents #typing.Final. """

  #: The inner type.
  wrapped: TypeArg


class NoReturn(Hint, t.NamedTuple):
  """ Represents #typing.NoReturn. """


class TypeGuard(Hint, t.NamedTuple):
  """ Represents #typing.TypeGuard. """

  #: The wrapped type.
  wrapped: TypeArg


class Literal(Hint, t.NamedTuple):
  """ Represents #typing.Literal. """

  #: The possible values represented by the literal.
  values: t.Tuple[t.Any, ...]


class NewType(Hint, t.NamedTuple):
  """ Represents #typing.NewType. """

  #: The name of the new type.
  name: str

  #: The underlying type for the new type.
  supertype: t.Type


class Unknown(Hint, t.NamedTuple):
  """ Represents an type hint that is not understood. """

  #: The type hint that was not understood.
  hint: t.Any
