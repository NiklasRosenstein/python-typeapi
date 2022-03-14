
import sys
import types
import typing as t
import typing_extensions as te

from .api import Annotated, Any, ClassVar, Final, ForwardRef, Hint, Literal, NewType, NoReturn, Type, TypeGuard, Union, Unknown
from .deconstruct import deconstruct_type, TypeInfo
from .utils import is_annotated_alias, is_generic, is_generic_alias, is_new_type, is_special_form, is_special_generic_alias, is_union_type

_TypeHintHandler = t.Callable[[t.Any], t.Optional[Hint]]
_handlers: t.List[_TypeHintHandler] = []


def _handler(func: _TypeHintHandler) -> _TypeHintHandler:
  """ Internal. Registers a type hint handler function. """

  _handlers.append(func)
  return func


@_handler
def _handle_any(hint: t.Any) -> t.Optional[Hint]:
  if hint is t.Any:
    return Any()
  return None


@_handler
def _handle_annotated(hint: t.Any) -> t.Optional[Hint]:
  if is_annotated_alias(hint):
    return Annotated(hint.__origin__, hint.__metadata__)
  return None


@_handler
def _handle_forward_ref(hint: t.Any) -> t.Optional[Hint]:
  if isinstance(hint, t.ForwardRef):
    return ForwardRef(hint.__forward_arg__, getattr(hint, '__forward_module__', None))
  elif isinstance(hint, str):
    return ForwardRef(hint, None)
  return None


@_handler
def _handle_class_var(hint: t.Any) -> t.Optional[Hint]:
  if is_generic_alias(hint) and hint.__origin__ == t.ClassVar:
    assert len(hint.__args__) == 1, hint
    return ClassVar(hint.__args__[0])
  return None


@_handler
def _handle_final(hint: t.Any) -> t.Optional[Hint]:
  if is_generic_alias(hint) and hint.__origin__ == te.Final:
    assert len(hint.__args__) == 1, hint
    return Final(hint.__args__[0])
  return None


@_handler
def _handle_no_return(hint: t.Any) -> t.Optional[Hint]:
  if hint == t.NoReturn:
    return NoReturn()
  return None


@_handler
def _handle_type_guard(hint: t.Any) -> t.Optional[Hint]:
  if is_generic_alias(hint) and hint.__origin__ == te.TypeGuard:
    assert len(hint.__args__) == 1, hint
    return TypeGuard(hint.__args__[0])
  return None


@_handler
def _handle_union(hint: t.Any) -> t.Optional[Hint]:
  if is_union_type(hint):
    assert len(hint.__args__) >= 2, hint
    return Union(hint.__args__)
  return None


@_handler
def _handle_literal(hint: t.Any) -> t.Optional[Hint]:
  if is_generic_alias(hint) and hint.__origin__ == te.Literal:
    assert len(hint.__args__) >= 1, hint
    return Literal(hint.__args__)
  return None


@_handler
def _handle_new_type(hint: t.Any) -> t.Optional[Hint]:
  if is_new_type(hint):
    return NewType(hint.__name__, hint.__supertype__)
  return None


@_handler
def _handle_generic_alias_of_concrete_type(hint: t.Any) -> t.Optional[Hint]:
  """ Handles #typing._GenericAlias and #types.GenericAlias objects that originate from a
  concrete type. This includes aliases for special generic aliases such as #typing.List, etc.
  because their `__origin__` points to the native Python type.

  !!! note

      It is important that this handler is run before #_handle_concrete_type(). Starting with
      Python 3.9, aliases of #typing.Generic subclasses are represented as instance of
      #types.GenericAlias, which in turn return positive if tested for `isinstance(alias, type)`
      and could thus be recognized as a concrete type.
  """

  if is_generic_alias(hint) and isinstance(hint.__origin__, type):
    return Type(hint.__origin__, hint.__args__)
  return None


@_handler
def _handle_concrete_type(hint: t.Any) -> t.Optional[Hint]:
  if isinstance(hint, type) and hint.__module__ not in ('typing', 'typing_extensions'):
    return Type(hint, None)
  return None


@_handler
def _handle_special_generic_alias(hint: t.Any) -> t.Optional[Hint]:
  if is_special_generic_alias(hint):
    return Type(hint.__origin__, None)
  return None


@t.overload
def parse_type_hint(hint: t.Any) -> Hint:
  """ Parse the given type hint to a #Hint object. If the type hint is not accepted by any of the
  handlers, an instance of #Unknown is returned instead.

  Arguments:
    hint: The type hint to adapt.
  Returns:
    A #Hint object that should make it easier to introspect the type hint with a stable API.
  """


@t.overload
def parse_type_hint(hint: t.Any, *, debug: te.Literal[True]) -> t.Tuple[Hint, t.Optional[str]]:
  """ Same as #parse_type_hint(), but returns the name of the handler function that accepted the
  type hint and converted it to a #Hint object. """


def parse_type_hint(hint: t.Any, *, debug: bool = False) -> t.Union[Hint, t.Tuple[Hint, t.Optional[str]]]:
  for handler in _handlers:
    result = handler(hint)
    if result is not None:
      return (result, handler.__name__) if debug else result
  return (Unknown(hint), None) if debug else Unknown(hint)
