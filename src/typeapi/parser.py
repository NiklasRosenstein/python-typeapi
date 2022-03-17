
import sys
import types
import typing as t
import typing_extensions as te

from .model import Annotated, Any, ClassVar, Final, ForwardRef, Hint, Literal, NewType, NoReturn, Type, TypeGuard, TypeVar, Union, Unknown
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
    return Annotated(parse_type_hint(hint.__origin__), hint.__metadata__)
  return None


@_handler
def _handle_forward_ref(hint: t.Any) -> t.Optional[Hint]:
  if isinstance(hint, t.ForwardRef):
    return ForwardRef(hint)
  elif isinstance(hint, str):
    return ForwardRef(t.ForwardRef(hint))
  return None


@_handler
def _handle_class_var(hint: t.Any) -> t.Optional[Hint]:
  if is_generic_alias(hint) and hint.__origin__ == t.ClassVar:
    assert len(hint.__args__) == 1, hint
    return ClassVar(parse_type_hint(hint.__args__[0]))
  return None


@_handler
def _handle_final(hint: t.Any) -> t.Optional[Hint]:
  if is_generic_alias(hint) and hint.__origin__ == te.Final:
    assert len(hint.__args__) == 1, hint
    return Final(parse_type_hint(hint.__args__[0]))
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
    return TypeGuard(parse_type_hint(hint.__args__[0]))
  return None


@_handler
def _handle_union(hint: t.Any) -> t.Optional[Hint]:
  if is_union_type(hint):
    assert len(hint.__args__) >= 2, hint
    return Union(tuple(parse_type_hint(a) for a in hint.__args__))
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
    return NewType(hint)
  return None


@_handler
def _handle_type_or_generic_alias(hint: t.Any) -> t.Optional[Hint]:
  """ Handles concrete types, generic aliases or special generic aliases using #Type.of(). """

  try:
    return Type.of(hint)
  except ValueError:
    return None


@_handler
def _handle_type_var(hint: t.Any) -> t.Optional[Hint]:
  if isinstance(hint, t.TypeVar):
    return TypeVar(hint)
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
