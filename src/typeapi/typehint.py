import abc
from typing import Dict, Union

from .utils import get_type_hint_args, get_type_hint_origin_or_none, get_type_hint_parameters

NoneType = type(None)


class _TypeHintMeta(abc.ABCMeta):
    """
    Meta class for :class:`TypeHint` to cache created instances and correctly
    instantiate the appropriate implementation based on the low-level type
    hint.
    """

    _cache: Dict[str, "TypeHint"] = {}

    def __call__(cls, hint: object) -> "TypeHint":  # type: ignore[override]
        # If the current class is not the base "TypeHint" class, we should let
        # object construction continue as usual.
        if cls is not TypeHint:
            return super().__call__(hint)  # type: ignore[no-any-return]

        # Otherwise, we are in this "TypeHint" class.

        # If the hint is a type hint in itself, we can return it as-is.
        if isinstance(hint, TypeHint):
            return hint

        # Check if the hint is already cached.
        hint_key = str(hint)
        if hint_key in cls._cache:
            return cls._cache[hint_key]

        # Create the wrapper for the low-level type hint.
        wrapper = cls._make_wrapper(hint)
        cls._cache[hint_key] = wrapper
        return wrapper

    def _make_wrapper(cls, hint: object) -> "TypeHint":
        """
        Create the :class:`TypeHint` implementation that wraps the given
        low-level type hint.
        """

        if hint is None:
            hint = NoneType

        origin = get_type_hint_origin_or_none(hint)
        if origin == Union:
            return UnionTypeHint(hint)
        elif str(origin).endswith(".Literal"):
            return LiteralTypeHint(hint)
        elif ".Annotated" in str(origin):
            return AnnotatedTypeHint(hint)

        return ClassTypeHint(hint)


class TypeHint(metaclass=_TypeHintMeta):
    """
    Base class that provides an object-oriented interface to a Python type hint.
    """

    def __init__(self, hint: object) -> None:
        self._hint = hint
        self._origin = get_type_hint_origin_or_none(hint)
        self._args = get_type_hint_args(hint)
        self._parameters = get_type_hint_parameters(hint)

    @property
    def hint(self) -> object:
        return self._hint

    @property
    def origin(self) -> object:
        return self._origin

    @property
    def args(self) -> object:
        return self._args

    @property
    def parameters(self) -> object:
        return self._parameters

    def __eq__(self, other: object) -> bool:
        if type(self) != type(other):
            return False
        assert isinstance(other, TypeHint)
        return (self.hint, self.origin, self.args, self.parameters) == (
            other.hint,
            other.origin,
            other.args,
            other.parameters,
        )


class ClassTypeHint(TypeHint):
    pass


class UnionTypeHint(TypeHint):
    pass


class LiteralTypeHint(TypeHint):
    pass


class AnnotatedTypeHint(TypeHint):
    pass
