
import dataclasses
import typing as t

from typeapi.deconstruct import TypeInfo, deconstruct_type
from .utils import TypeArg, type_repr


@dataclasses.dataclass
class Hint:
  """ Base for classes that represent type hints. """

  #: The original #typing hint.
  source: t.Any = dataclasses.field(repr=False)

  def __post_init__(self) -> None:
    if type(self) is Hint:
      raise TypeError('Hint cannot be constructed')


@dataclasses.dataclass
class Type(Hint):
  """ Represents a concrete type, including type arguments if applicable. """

  #: The native Python type. Note that this may be #types.NoneType if the type hint
  #: represented is `None`.
  type: t.Type

  def __post_init__(self) -> None:
    self._info: t.Optional[TypeInfo] = None

  def __repr__(self) -> str:
    if self.args is None:
      return '{}({})'.format(self.__class__.__name__, type_repr(self.type))
    return '{}({}, ({}))'.format(self.__class__.__name__, type_repr(self.type), ', '.join(map(type_repr, self.args)))

  @property
  def info(self) -> TypeInfo:
    """ Return the deconstructed #TypeInfo for the original type hint, providing information on the number of type
    arguments, the type parameters and type arguments (if the type hint was a generic alias). """

    if self._info is None:
      self._info = deconstruct_type(self.source)
    return self._info

  @property
  def args(self) -> t.Optional[t.Tuple[TypeArg, ...]]:
    """ The type arguments, if applicable. This may yet contain type variables if that is what the original generic
    alias was created with. This is an alias for accesing #TypeInfo.args from #info. """

    return self.info.args


@dataclasses.dataclass
class Union(Hint):
  """ Represents #typing.Union or #typing.Optional. """

  #: The types in this union.
  types: t.Tuple[TypeArg, ...]


@dataclasses.dataclass
class Annotated(Hint):
  """ Represents a type wrapped in #typing.Annotated. """

  #: The type that is annotated.
  wrapped: TypeArg

  #: The metadata in the annotation.
  metadata: t.Tuple[t.Any, ...]

  def __repr__(self) -> str:
    return 'Annotated({}, {})'.format(type_repr(self.wrapped), ', '.join(map(repr, self.metadata)))


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
  wrapped: TypeArg


@dataclasses.dataclass
class Final(Hint):
  """ Represents #typing.Final. """

  #: The inner type.
  wrapped: TypeArg


@dataclasses.dataclass
class NoReturn(Hint):
  """ Represents #typing.NoReturn. """


@dataclasses.dataclass
class TypeGuard(Hint):
  """ Represents #typing.TypeGuard. """

  #: The wrapped type.
  wrapped: TypeArg


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
