
import collections
from typing import Any, Optional, TypeVar

import warnings
import sys

IS_PYTHON_AT_LAST_3_6 = sys.version_info[:2] <= (3, 6)
IS_PYTHON_AT_LAST_3_8 = sys.version_info[:2] <= (3, 8)
IS_PYTHON_AT_LEAST_3_7 = sys.version_info[:2] >= (3, 7)
IS_PYTHON_AT_LEAST_3_9 = sys.version_info[:2] >= (3, 9)
TYPING_MODULE_NAMES = frozenset(["typing", "typing_extensions"])


def get_type_hint_origin_or_none(hint: object) -> Optional[Any]:
    """
    Returns the origin type of a low-level type hint, or None.
    """

    hint_origin = getattr(hint, '__origin__', None)

    # In Python 3.6, List[int].__origin__ points to List; but we can look for
    # the Python native type in its __bases__.
    if IS_PYTHON_AT_LAST_3_6 and hasattr(hint, "__orig_bases__"):

        if hint.__name__ == "Annotated" and hint.__args__:
            from typing_extensions import Annotated
            return Annotated

        # Find a non-typing base class, which represents the actual Python type
        # for this type hint.
        bases = tuple(x for x in (hint_origin or hint).__orig_bases__ if x.__module__ != 'typing')
        if len(bases) == 1:
            hint_origin = bases[0]
        elif len(bases) > 1:
            raise RuntimeError(
                f"expected only one non-typing class in __orig_bases__ in type hint {hint!r}, got {bases!r}"
            )
        else:
            # If we have a same-named type in collections.abc; use that.
            type_name = hint.__name__
            if hasattr(collections.abc, type_name):
                hint_origin = getattr(collections.abc, type_name)

    elif IS_PYTHON_AT_LAST_3_6 and type(hint).__name__ == "_Literal" and hint.__values__ is not None:
        from typing_extensions import Literal

        hint_origin = Literal

    elif not IS_PYTHON_AT_LAST_3_6 and type(hint).__name__ == "_AnnotatedAlias":
        from typing_extensions import Annotated

        return Annotated

    return hint_origin


def get_type_hint_args(hint: object) -> tuple:
    """
    Returns the arguments of a low-level type hint. An empty tuple is returned
    if the hint is unparameterized.
    """

    hint_args = getattr(hint, "__args__", None) or ()

    # In Python 3.7 and 3.8, generics like List and Tuple have a "_special"
    # but their __args__ contain type vars. For consistent results across
    # Python versions, we treat those as having no arguments (as they have
    # not been explicitly parametrized by the user).
    if IS_PYTHON_AT_LEAST_3_7 and IS_PYTHON_AT_LAST_3_8 and getattr(hint, "_special", False):
        hint_args = ()

    # If we have an "Annotated" hint, we need to do some restructuring of the args.
    if (
        IS_PYTHON_AT_LAST_3_6 and getattr(hint, "__name__", None) == "Annotated" and
        getattr(hint, "__module__", None) in TYPING_MODULE_NAMES and hint_args
    ):
        # In Python 3.6, Annotated is only available through
        # typing_extensions, where the second tuple element contains the
        # metadata.
        assert len(hint_args) == 2 and isinstance(hint_args[1], tuple), hint_args
        hint_args = (hint_args[0],) + hint_args[1]
    elif not IS_PYTHON_AT_LAST_3_6 and type(hint).__name__ == "_AnnotatedAlias":
        hint_args += hint.__metadata__

    if not hint_args and IS_PYTHON_AT_LAST_3_6:
        hint_args = getattr(hint, "__values__", None) or ()

    return hint_args


def get_type_hint_parameters(hint: object) -> tuple:
    """
    Returns the parameters of a type hint, i.e. the tuple of type variables.
    """

    hint_params = getattr(hint, "__parameters__", None) or ()

    # In Python 3.9+, special generic aliases like List and Tuple don't store
    # their type variables as parameters anymore; we try to restore those.
    if IS_PYTHON_AT_LEAST_3_9 and getattr(hint, "_nparams", 0) > 0:
        type_hint_name = getattr(hint, "_name", None) or hint.__name__
        if type_hint_name in _SPECIAL_ALIAS_TYPEVARS:
            return tuple(get_type_var_from_string_repr(x) for x in _SPECIAL_ALIAS_TYPEVARS[type_hint_name])

        warnings.warn(
            "The following type hint appears like a special generic alias but its type parameters are not "
            f"known to `typeapi`: {hint}",
            UserWarning,
        )

    return hint_params


def get_type_var_from_string_repr(type_var_repr: str) -> object:
    """
    Returns a :class:`TypeVar` for its string rerpesentation.
    """

    if type_var_repr in _TYPEVARS_CACHE:
        return _TYPEVARS_CACHE[type_var_repr]

    if type_var_repr.startswith("~"):
        covariant = False
        contravariant = False
    elif type_var_repr.startswith("+"):
        covariant = True
        contravariant = False
    elif type_var_repr.startswith("-"):
        covariant = False
        contravariant = True
    else:
        raise ValueError(f"invalid TypeVar string: {type_var_repr!r}")

    type_var_name = type_var_repr[1:]
    type_var = TypeVar(type_var_name, covariant=covariant, contravariant=contravariant)  # type: ignore
    _TYPEVARS_CACHE[type_var_repr] = type_var
    return type_var


# Generated in Python 3.8 with scripts/dump_type_vars.py.
# We use this map to create TypeVars in get_type_hint_parameters() on the fly
# for Python 3.9+ since they no longer come with this information embedded.
_SPECIAL_ALIAS_TYPEVARS = {
  'Awaitable': ['+T_co'],
  'Coroutine': ['+T_co', '-T_contra', '+V_co'],
  'AsyncIterable': ['+T_co'],
  'AsyncIterator': ['+T_co'],
  'Iterable': ['+T_co'],
  'Iterator': ['+T_co'],
  'Reversible': ['+T_co'],
  'Container': ['+T_co'],
  'Collection': ['+T_co'],
  'AbstractSet': ['+T_co'],
  'MutableSet': ['~T'],
  'Mapping': ['~KT', '+VT_co'],
  'MutableMapping': ['~KT', '~VT'],
  'Sequence': ['+T_co'],
  'MutableSequence': ['~T'],
  'List': ['~T'],
  'Deque': ['~T'],
  'Set': ['~T'],
  'FrozenSet': ['+T_co'],
  'MappingView': ['+T_co'],
  'KeysView': ['~KT'],
  'ItemsView': ['~KT', '+VT_co'],
  'ValuesView': ['+VT_co'],
  'ContextManager': ['+T_co'],
  'AsyncContextManager': ['+T_co'],
  'Dict': ['~KT', '~VT'],
  'DefaultDict': ['~KT', '~VT'],
  'OrderedDict': ['~KT', '~VT'],
  'Counter': ['~T'],
  'ChainMap': ['~KT', '~VT'],
  'Generator': ['+T_co', '-T_contra', '+V_co'],
  'AsyncGenerator': ['+T_co', '-T_contra'],
  'Type': ['+CT_co'],
  'SupportsAbs': ['+T_co'],
  'SupportsRound': ['+T_co'],
  'IO': ['~AnyStr'],
  'Pattern': ['~AnyStr'],
  'Match': ['~AnyStr'],
}

_TYPEVARS_CACHE = {
    "~AnyStr": TypeVar("AnyStr", bytes, str),
    "~CT_co": TypeVar("CT_co", covariant=True, bound=type),
}
