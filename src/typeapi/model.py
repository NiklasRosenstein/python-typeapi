
from __future__ import annotations
import dataclasses
import sys
import typing as t
from . import utils


class Hint:
  """ Base for classes that represent type hints. """

  def __init__(self, *args, **kwargs) -> None:
    if type(self) is Hint:
      raise TypeError('Hint cannot be constructed')

  def __repr__(self) -> str:
    return f'{type(self).__name__}({", ".join(repr(getattr(self, f.name)) for f in dataclasses.fields(self))})'

  def visit(self, func: t.Callable[[Hint], Hint]) -> Hint:
    """ Visit the hint and its subhints, if any, and call *func* on it. Returns the result of *func* on self. """

    return func(self)


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
  args: t.Optional[t.Tuple[Hint, ...]]

  def __init__(
    self,
    type_: t.Type,
    nparams: int = 0,
    parameters: t.Optional[t.Tuple[t.Union[t.Any, t.TypeVar], ...]] = None,
    args: t.Optional[t.Tuple[Hint, ...]] = None,
  ) -> None:
    # NOTE (@NiklasRosenstein): Mypy thinks type vars are "objects", not t.TypeVar. To simplify code that
    # constructs an instance of this class, we accept Any but ensure it is a t.TypeVar at runtime.
    assert parameters is None or all(isinstance(v, t.TypeVar) for v in parameters)
    assert isinstance(type_, type), type_
    self.type = type_
    self.nparams = nparams
    self.parameters = parameters
    self.args = args

  def __repr__(self) -> str:
    parts = [utils.type_repr(self.type)]
    if self.nparams != 0:
      parts.append(f'nparams={self.nparams}')
    if self.parameters is not None:
      parts.append(f'parameters={self.parameters!r}')
    if self.args is not None:
      parts.append(f'args=({", ".join(map(utils.type_repr, self.args))})')
    return f'Type({", ".join(parts)})'

  def with_args(self, args: t.Optional[t.Tuple[Hint, ...]]) -> Type:
    """ Return a copy of the #Type object, but #args replaced by the *args* parameter value. """

    return Type(self.type, self.nparams, self.parameters, args)

  def get_parameter_mapping(self) -> t.Dict[t.TypeVar, Hint]:
    """ Computes the values assigned to all type parameters present in *type* and its bases. """

    # TODO (@NiklasRosenstein): This might be a good spot to implement caching.

    type_parameters = dict(zip(self.parameters or (), self.args or ()))
    if utils.is_generic(self.type):
      for base in self.type.__orig_bases__:
        type_parameters = {**Type.of(base).get_parameter_mapping(), **type_parameters}
    return type_parameters

  def get_orig_bases(self, all_: bool = False) -> t.Iterable[utils.GenericAlias]:
    """ A generator for the generic aliases that comprise the generic base classes of #type. Note that if #args
    is not `None`, it means this #Type object was created from a generic alias, but that generic alias is not
    returned by this generator.

    Arguments:
      all_: If set to `True`, all original bases in the entire class hierarchy will be returned.
    """

    if not utils.is_generic(self.type):
      return

    # TODO (@NiklasRosenstein): If two bases have the same common base, the native type.__mro__ actually
    #   returns that commonly shared base after the bases that share it, but with the below way of iterating
    #   over the bases, we will end up yielding it after the first base.
    seen = set()
    for base in self.type.__orig_bases__:
      if not utils.is_generic_alias(base):
        assert isinstance(base, type), base
        continue
      if base in seen: continue
      seen.add(base)
      yield base

      if all_:
        for base2 in Type.of(base).get_orig_bases(True):
          if base2 in seen: continue
          seen.add(base2)
          yield base2

  def get_orig_bases_parametrized(self, all_: bool = False) -> t.Dict[utils.GenericAlias, Type]:
    """ Create a dictionary that maps the generic aliases returned by #get_orig_bases() to a type hint infused
    with the current type's #args. If the #type is not a generic or has no generic bases, this method returns
    an empty dictionary. Note that this will skip #typing.Generic. """

    type_parameters = self.get_parameter_mapping()
    result = {}
    for base in self.get_orig_bases():
      if base.__origin__ is t.Generic: continue
      type_ = Type.of(base)
      result[base] = infuse_type_parameters(type_, type_parameters)
      if all_:
        result = {**type_.get_orig_bases_parametrized(True), **result}
    return result

  def visit(self, func: t.Callable[[Hint], Hint]) -> Hint:
    return func(self.with_args(tuple(a.visit(func) for a in self.args) if self.args is not None else None))

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

    # TODO (@NiklasRosenstein): This might be a good spot to implement caching.

    import typeapi

    def _raise() -> t.NoReturn: raise ValueError(f'unable to deconstruct {type_!r}')

    if type_ is t.Any:
      return Type(object, 0, None, None)

    if type_ is t.Generic:
      return Type(t.Generic, 0, None, None)  # type: ignore[arg-type]

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
      elif utils.is_generic(type_.__origin__) or type_.__origin__ == t.Generic:
        type_info = Type.of(type_.__origin__)

      else:
        _raise()

      return type_info.with_args(tuple(typeapi.of(th) for th in type_.__args__))

    if utils.is_generic(type_):
      return Type(type_, len(type_.__parameters__), type_.__parameters__, None)

    # NOTE: It is important to run the isinstance() check here after testing for is_generic_alias(), because
    # starting with Python 3.10, instances of #types.GenericAlias test positive for isinstance(..., type).
    if isinstance(type_, type) and type_.__module__ not in ('typing', 'typing_extensions'):
      # NOTE: We don't want for example #typing.NewType (the class, not an instance of it) to be treated as a type.
      # With this block, we prevent types of the #typing module to be themselves represented as a #Type by typeapi.
      return Type(type_, 0, None, None)

    _raise()


@dataclasses.dataclass(repr=False)
class Union(Hint):
  """ Represents #typing.Union or #typing.Optional. """

  #: The types in this union.
  types: t.Tuple[Hint, ...]

  def __post_init__(self) -> None:
    assert len(self.types) >= 2, self.types

  def has_none_type(self) -> bool:
    """ Returns `True` if one of the #types is a #Type representing #types.NoneType. """

    return any(th for th in self.types if isinstance(th, Type) and th.type == type(None))

  def without_none_type(self) -> Hint:
    """ Return a copy but with #types not containing a #types.NoneType. If there is only one member remaining,
    that member type hint will be returned directly (because #Union must contain at least two members). """

    types = tuple(th for th in self.types if not (isinstance(th, Type) and th.type == type(None)))
    if len(types) == 1:
      return types[0]
    return Union(types)

  def visit(self, func: t.Callable[[Hint], Hint]) -> Hint:
    return func(Union(tuple(th.visit(func) for th in self.types)))


@dataclasses.dataclass(repr=False)
class Annotated(Hint):
  """ Represents a type wrapped in #typing.Annotated. """

  #: The type that is annotated.
  wrapped: Hint

  #: The metadata in the annotation.
  metadata: t.Tuple[t.Any, ...]

  def visit(self, func: t.Callable[[Hint], Hint]) -> Hint:
    return func(Annotated(self.wrapped.visit(func), self.metadata))


@dataclasses.dataclass(repr=False)
class ForwardRef(Hint):
  """ Represents a forward reference. """

  #: The forward reference.
  ref: t.ForwardRef

  def __repr__(self) -> str:
    return str(self.ref)

  @property
  def expr(self) -> str:
    """ Returns the code from the forward reference. """

    return self.ref.__forward_arg__

  @property
  def module(self) -> t.Optional[str]:
    """ Returns the name of the moduel in which the forward reference is to be evaluated. """

    return getattr(self.ref, '__forward_module__', None)

  def evaluate(
    self,
    fallback_module: t.Optional[str] = None,
    globalns: t.Optional[t.Dict[str, t.Any]] = None,
    localns: t.Optional[t.Dict[str, t.Any]] = None,
  ) -> t.Any:
    """ Evaluate the forward reference, preferably in the module that is already known by #ref, or otherwise
    in the specified *fallback_module* or the specified *globalns* and *localns* namespaces.. """

    module_name = self.module or fallback_module
    if module_name:
      globalns = vars(sys.modules[module_name])
      localns = None
    else:
      if globalns is None and localns is None:
        raise RuntimeError(f'no module or namespace to evaluate {self}')
    if sys.version_info[:2] < (3, 9):
      return self.ref._evaluate(globalns, localns)
    else:
      return self.ref._evaluate(globalns, localns, set())  # type: ignore[call-arg]  # mypy doesn't know about the third arg


@dataclasses.dataclass(repr=False)
class Any(Hint):  # type: ignore[misc]
  """ Represents #typing.Any. """


@dataclasses.dataclass(repr=False)
class ClassVar(Hint):
  """ Represents #typing.ClassVar. """

  #: The inner type.
  wrapped: Hint

  def visit(self, func: t.Callable[[Hint], Hint]) -> Hint:
    return func(ClassVar(self.wrapped.visit(func)))


@dataclasses.dataclass(repr=False)
class Final(Hint):
  """ Represents #typing.Final. """

  #: The inner type.
  wrapped: Hint

  def visit(self, func: t.Callable[[Hint], Hint]) -> Hint:
    return func(Final(self.wrapped.visit(func)))


@dataclasses.dataclass(repr=False)
class NoReturn(Hint):
  """ Represents #typing.NoReturn. """


@dataclasses.dataclass(repr=False)
class TypeGuard(Hint):
  """ Represents #typing.TypeGuard. """

  #: The wrapped type.
  wrapped: Hint

  def visit(self, func: t.Callable[[Hint], Hint]) -> Hint:
    return func(TypeGuard(self.wrapped.visit(func)))


@dataclasses.dataclass(repr=False)
class Literal(Hint):
  """ Represents #typing.Literal. """

  #: The possible values represented by the literal.
  values: t.Tuple[t.Any, ...]


@dataclasses.dataclass(repr=False)
class TypeVar(Hint):
  """ Represents a #typing.TypeVar. """

  #: The type variable.
  var: t.TypeVar

  def __init__(self, var: t.Union[t.Any, t.TypeVar]) -> None:
    # NOTE (@NiklasRosenstein): Mypy thinks type vars are "objects", not t.TypeVar. To simplify code that
    # constructs an instance of this class, we accept Any but ensure it is a t.TypeVar at runtime.
    assert isinstance(var, t.TypeVar), var
    self.var = var


@dataclasses.dataclass(repr=False)
class NewType(Hint):
  """ Represents #typing.NewType. """

  #: The typing new type instance.
  type: utils.NewType

  @property
  def name(self) -> str:
    """ The name of the new type. """

    return self.type.__name__

  @property
  def supertype(self) -> t.Type:
    """ The underlying type of the new type. """

    return self.type.__supertype__


@dataclasses.dataclass(repr=False)
class Unknown(Hint):
  """ Represents an type hint that is not understood. """

  #: The type hint that could not be converted into the typeapi.
  hint: t.Any


def eval_types(
  hint: Hint,
  module: t.Optional[str] = None,
  globalns: t.Optional[t.Dict[str, t.Any]] = None,
  localns: t.Optional[t.Dict[str, t.Any]] = None,
) -> Hint:
  """ Evaluate all forward references present in *hint*.

  Arguments:
    hint: The #typeapi #Hint to evaluate forward references in.
    module: The name of the module to evaluate the references in if they are not already associated with a module.
      Note that the module must be present in #sys.modules.
    globalns: A mapping to serve as a namespace to evaluate forward references in if *module* is not set and the
      forward reference has no module reference.
    localns: Same as *globalns* but for the local namespace.
  Returns:
    The same hint with all forward references replaced.
  """

  import typeapi

  def _visitor(hint: Hint) -> Hint:
    if isinstance(hint, ForwardRef):
      return typeapi.of(hint.evaluate(module, globalns, localns))
    return hint

  return hint.visit(_visitor)


@t.overload
def infuse_type_parameters(hint: Type, parameters: t.Dict[t.TypeVar, Hint]) -> Type:
  """ If you already have a #Type hint, infusing it returns just another #Type. """


@t.overload
def infuse_type_parameters(hint: Hint, parameters: t.Dict[t.TypeVar, Hint]) -> Hint:
  """ Replace type variables in *hint* with the parameters in the given mapping. """


def infuse_type_parameters(hint: Hint, parameters: t.Dict[t.TypeVar, Hint]) -> Hint | Type:
  if not parameters:
    return hint

  def _visitor(hint: Hint) -> Hint:
    # Make sure we resolve chains of parameter mappings (e.g. {T: U, U: int}).
    while isinstance(hint, TypeVar) and hint.var in parameters:
      hint = parameters[hint.var]
    return hint

  new_hint = hint.visit(_visitor)
  if isinstance(hint, Type):
    assert isinstance(new_hint, Type)
  return new_hint


def unwrap(hint: Hint) -> t.Tuple[Hint, t.Tuple[t.Any, ...]]:
  """ If given a #typing.Annotated hint, returns the wrapped hint and the annotation metadata. Otherwise, the
  *hint* is returned as-is and an empty tuple for metadata. """

  if isinstance(hint, Annotated):
    return hint.wrapped, hint.metadata
  return hint, ()
