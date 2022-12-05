import collections
import inspect
import sys
import types
import typing
import warnings
from types import FrameType, FunctionType, ModuleType
from typing import Any, Callable, Dict, Generic, Optional, Set, Tuple, TypeVar, Union, get_type_hints as _get_type_hints

import typing_extensions
from typing_extensions import Protocol, TypeGuard

IS_PYTHON_AT_LAST_3_6 = sys.version_info[:2] <= (3, 6)
IS_PYTHON_AT_LAST_3_8 = sys.version_info[:2] <= (3, 8)
IS_PYTHON_AT_LEAST_3_7 = sys.version_info[:2] >= (3, 7)
IS_PYTHON_AT_LEAST_3_9 = sys.version_info[:2] >= (3, 9)
IS_PYTHON_AT_LEAST_3_10 = sys.version_info[:2] >= (3, 10)
TYPING_MODULE_NAMES = frozenset(["typing", "typing_extensions", "collections.abc"])
T_contra = TypeVar("T_contra", contravariant=True)
U_co = TypeVar("U_co", covariant=True)

if sys.version_info[:2] <= (3, 6):
    from typing import _ForwardRef as ForwardRef
else:
    from typing import ForwardRef

__all__ = [
    "ForwardRef",
    "get_type_hint_origin_or_none",
    "get_type_hint_args",
    "get_type_hint_parameters",
    "get_type_var_from_string_repr",
    "type_repr",
    "get_annotations",
    "TypedDictProtocol",
    "is_typed_dict",
]


def get_type_hint_origin_or_none(hint: object) -> "Any | None":
    """
    Returns the origin type of a low-level type hint, or None.
    """

    hint_origin = getattr(hint, "__origin__", None)

    # In Python 3.6, List[int].__origin__ points to List; but we can look for
    # the Python native type in its __bases__.
    if (
        IS_PYTHON_AT_LAST_3_6
        and hasattr(hint, "__orig_bases__")
        and getattr(hint, "__module__", None) in TYPING_MODULE_NAMES
    ):

        if hint.__name__ == "Annotated" and hint.__args__:  # type: ignore
            from typing_extensions import Annotated

            return Annotated

        # Find a non-typing base class, which represents the actual Python type
        # for this type hint.
        bases = tuple(
            x
            for x in (hint_origin or hint).__orig_bases__  # type: ignore
            if x.__module__ not in TYPING_MODULE_NAMES and not hasattr(x, "__orig_bases__")
        )
        if len(bases) == 1:
            hint_origin = bases[0]
        elif len(bases) > 1:
            raise RuntimeError(
                f"expected only one non-typing class in __orig_bases__ in type hint {hint!r}, got {bases!r}"
            )
        else:
            # If we have a same-named type in collections.abc; use that.
            type_name = hint.__name__  # type: ignore
            if hasattr(collections.abc, type_name):
                hint_origin = getattr(collections.abc, type_name)

        return hint_origin

    elif IS_PYTHON_AT_LAST_3_6 and type(hint).__name__ == "_Literal" and hint.__values__ is not None:  # type: ignore
        from typing_extensions import Literal

        return Literal

    elif not IS_PYTHON_AT_LAST_3_6 and type(hint).__name__ == "_AnnotatedAlias":  # type: ignore
        from typing_extensions import Annotated

        return Annotated

    elif IS_PYTHON_AT_LEAST_3_10 and isinstance(hint, types.UnionType):  # type: ignore[attr-defined]
        return Union

    if hint_origin is None and hint == Any:
        return object

    return hint_origin


def get_type_hint_original_bases(hint: object) -> "Tuple[Any, ...] | None":
    """
    Returns the original bases of a generic type.
    """

    orig_bases = getattr(hint, "__orig_bases__", None)

    if orig_bases is not None and IS_PYTHON_AT_LAST_3_6 and getattr(hint, "__args__", None):
        orig_bases = None

    return orig_bases


def get_type_hint_args(hint: object) -> Tuple[Any, ...]:
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
        IS_PYTHON_AT_LAST_3_6
        and getattr(hint, "__name__", None) == "Annotated"
        and getattr(hint, "__module__", None) in TYPING_MODULE_NAMES
        and hint_args
    ):
        # In Python 3.6, Annotated is only available through
        # typing_extensions, where the second tuple element contains the
        # metadata.
        assert len(hint_args) == 2 and isinstance(hint_args[1], tuple), hint_args
        hint_args = (hint_args[0],) + hint_args[1]
    elif not IS_PYTHON_AT_LAST_3_6 and type(hint).__name__ == "_AnnotatedAlias":
        hint_args += hint.__metadata__  # type: ignore

    if not hint_args and IS_PYTHON_AT_LAST_3_6:
        hint_args = getattr(hint, "__values__", None) or ()

    return hint_args


def get_type_hint_parameters(hint: object) -> Tuple[Any, ...]:
    """
    Returns the parameters of a type hint, i.e. the tuple of type variables.
    """

    hint_params = getattr(hint, "__parameters__", None) or ()

    # In Python 3.9+, special generic aliases like List and Tuple don't store
    # their type variables as parameters anymore; we try to restore those.
    if IS_PYTHON_AT_LEAST_3_9 and getattr(hint, "_nparams", 0) > 0:
        type_hint_name = getattr(hint, "_name", None) or hint.__name__  # type: ignore
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

    type_var_name = type_var_repr[1:]  # noqa: F841
    type_var = TypeVar(type_var_name, covariant=covariant, contravariant=contravariant)  # type: ignore
    _TYPEVARS_CACHE[type_var_repr] = type_var
    return type_var


def get_subscriptable_type_hint_from_origin(origin: object, *, __cache: Dict[Any, Any] = {}) -> Any:
    """Given any type, returns its corresponding subscriptable version. This
    is the type itself in most cases (assuming it is a subclass of
    :class:`typing.Generic`), but for special types such as :class:`list` or
    :class:`collections.abc.Sequence`, it returns the respective special alias
    from the :mod:`typing` module instead."""

    if not __cache:
        if sys.version_info[:2] <= (3, 6):
            attr = "__extra__"
        else:
            attr = "__origin__"

        def _populate(hint: Any) -> None:
            origin = getattr(hint, attr, None)
            if origin is not None:
                __cache[origin] = hint

        for value in vars(typing).values():
            _populate(value)
        for value in vars(typing_extensions).values():
            _populate(value)

    return __cache.get(origin, origin)


# Generated in Python 3.8 with scripts/dump_type_vars.py.
# We use this map to create TypeVars in get_type_hint_parameters() on the fly
# for Python 3.9+ since they no longer come with this information embedded.
_SPECIAL_ALIAS_TYPEVARS = {
    "Awaitable": ["+T_co"],
    "Coroutine": ["+T_co", "-T_contra", "+V_co"],
    "AsyncIterable": ["+T_co"],
    "AsyncIterator": ["+T_co"],
    "Iterable": ["+T_co"],
    "Iterator": ["+T_co"],
    "Reversible": ["+T_co"],
    "Container": ["+T_co"],
    "Collection": ["+T_co"],
    "AbstractSet": ["+T_co"],
    "MutableSet": ["~T"],
    "Mapping": ["~KT", "+VT_co"],
    "MutableMapping": ["~KT", "~VT"],
    "Sequence": ["+T_co"],
    "MutableSequence": ["~T"],
    "List": ["~T"],
    "Deque": ["~T"],
    "Set": ["~T"],
    "FrozenSet": ["+T_co"],
    "MappingView": ["+T_co"],
    "KeysView": ["~KT"],
    "ItemsView": ["~KT", "+VT_co"],
    "ValuesView": ["+VT_co"],
    "ContextManager": ["+T_co"],
    "AsyncContextManager": ["+T_co"],
    "Dict": ["~KT", "~VT"],
    "DefaultDict": ["~KT", "~VT"],
    "OrderedDict": ["~KT", "~VT"],
    "Counter": ["~T"],
    "ChainMap": ["~KT", "~VT"],
    "Generator": ["+T_co", "-T_contra", "+V_co"],
    "AsyncGenerator": ["+T_co", "-T_contra"],
    "Type": ["+CT_co"],
    "SupportsAbs": ["+T_co"],
    "SupportsRound": ["+T_co"],
    "IO": ["~AnyStr"],
    "Pattern": ["~AnyStr"],
    "Match": ["~AnyStr"],
}

_TYPEVARS_CACHE = {
    "~AnyStr": TypeVar("AnyStr", bytes, str),
    "~CT_co": TypeVar("CT_co", covariant=True, bound=type),
}


def type_repr(obj: Any) -> str:
    """#typing._type_repr() stolen from Python 3.8."""

    if (getattr(obj, "__module__", None) or getattr(type(obj), "__module__", None)) in TYPING_MODULE_NAMES or hasattr(
        obj, "__args__"
    ):
        # NOTE(NiklasRosenstein): In Python 3.6, List[int] is actually a "type" subclass so we can't
        #       rely on the fall through on the below.
        return repr(obj)

    if isinstance(obj, type):
        if obj.__module__ == "builtins":
            return obj.__qualname__
        return f"{obj.__module__}.{obj.__qualname__}"
    if obj is ...:
        return "..."
    if isinstance(obj, FunctionType):
        return obj.__name__
    return repr(obj)


def get_annotations(
    obj: Union[Callable[..., Any], ModuleType, type],
    include_bases: bool = False,
    globalns: Optional[Dict[str, Any]] = None,
    localns: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Like #typing.get_type_hints(), but always includes extras. This is important when we want to inspect
    #typing.Annotated hints (without extras the annotations are removed). In Python 3.10 and onwards, this is
    an alias for #inspect.get_annotations() with `eval_str=True`.

    If *include_bases* is set to `True`, annotations from base classes are taken into account as well.

    This function will take into account the locals and globals accessible through the frame associated with
    a function or type by the #scoped() decorator."""

    if hasattr(obj, "__typeapi_frame__"):
        frame: FrameType = obj.__typeapi_frame__  # type: ignore[union-attr]
        globalns = frame.f_globals
        localns = frame.f_locals
        del frame

    if sys.version_info[:2] <= (3, 9):
        if not include_bases and "__annotations__" not in vars(obj):
            # Handle case when class has no explicit annotations, see python-typeapi#3
            return {}
        if sys.version_info[:2] <= (3, 8):
            annotations = _get_type_hints(obj, globalns=globalns, localns=localns)
        else:
            annotations = _get_type_hints(obj, globalns=globalns, localns=localns, include_extras=True)
        if not include_bases:
            # To replicate the behaviour of #inspect.get_annotations(), which is to _not_ take into account
            # the annotations of the base class, we discard all entries from the resulting dictionary that
            # is not included in the types __annotations__.
            local_annotations = getattr(obj, "__annotations__", {})
            return {k: v for k, v in annotations.items() if k in local_annotations}
        return annotations
    elif isinstance(obj, type) and include_bases:
        annotations = {}
        for cls in obj.__mro__:
            annotations.update(
                {
                    k: v
                    for k, v in inspect.get_annotations(cls, globals=globalns, locals=localns, eval_str=True).items()
                    if k not in annotations
                }
            )
        return annotations
    else:
        return inspect.get_annotations(obj, globals=globalns, locals=localns, eval_str=True)


class TypedDictProtocol(Protocol):
    """A protocol that describes #typing.TypedDict values (which are actually instances of the #typing._TypedDictMeta
    metaclass). Use #is_typed_dict() to check if a hint is matches this protocol."""

    __annotations__: Dict[str, Any]
    __required_keys__: Set[str]
    __optional_keys__: Set[str]
    __total__: bool


def is_typed_dict(hint: Any) -> TypeGuard[TypedDictProtocol]:
    """
    Returns:
        `True` if *hint* is a #typing.TypedDict.

    !!! note

        Typed dictionaries are actually just type objects. This means #typeapi.of() will represent them as
        #typeapi.models.Type.
    """

    import typing

    import typing_extensions

    for m in (typing, typing_extensions):
        if hasattr(m, "_TypedDictMeta") and isinstance(hint, m._TypedDictMeta):  # type: ignore[attr-defined]
            return True
    return False


class HasGetitem(Protocol, Generic[T_contra, U_co]):
    def __getitem__(self, __key: T_contra) -> U_co:
        ...
