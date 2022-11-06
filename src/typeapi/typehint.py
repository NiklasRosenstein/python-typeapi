import abc
from typing import Any, Dict, List, Tuple, TypeVar, Union, overload

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
        elif isinstance(hint, TypeVar):
            return TypeVarTypeHint(hint)

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
    def args(self) -> Tuple[Any, ...]:
        return self._args

    @property
    def parameters(self) -> Tuple[Any, ...]:
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

    def __len__(self) -> int:
        return len(self.args)

    @overload
    def __getitem__(self, __index: int) -> "TypeHint":
        ...

    @overload
    def __getitem__(self, __slice: slice) -> List["TypeHint"]:
        ...

    def __getitem__(self, index: "int | slice") -> "TypeHint | List[TypeHint]":
        if isinstance(index, int):
            return TypeHint(self.args[index])
        else:
            return [TypeHint(x) for x in self.args[index]]


class ClassTypeHint(TypeHint):
    def __init__(self, hint: object) -> None:
        super().__init__(hint)
        assert isinstance(self.hint, type) or isinstance(self.origin, type), (
            "ClassTypeHint must be initialized from a real type or a generic that points to a real type. "
            f'Got "{self.hint!r}" with origin "{self.origin}"'
        )

    @property
    def type(self) -> type:
        if isinstance(self.origin, type):
            return self.origin
        if isinstance(self.hint, type):
            return self.hint
        assert False, "ClassTypeHint not initialized from a real type or a generic that points to a real type."


class UnionTypeHint(TypeHint):
    pass


class LiteralTypeHint(TypeHint):
    @property
    def args(self) -> Tuple[Any, ...]:
        return ()

    def __len__(self) -> int:
        return 0

    @property
    def values(self) -> Tuple[Any, ...]:
        return self._args


class AnnotatedTypeHint(TypeHint):
    @property
    def args(self) -> Tuple[Any, ...]:
        return (self._args[0],)

    def __len__(self) -> int:
        return 1

    @property
    def metadata(self) -> Tuple[Any, ...]:
        return self._args[1:]


class TypeVarTypeHint(TypeHint):
    @property
    def hint(self) -> TypeVar:
        assert isinstance(self._hint, TypeVar)
        return self._hint

    @property
    def name(self) -> str:
        return self.hint.__name__

    @property
    def covariant(self) -> bool:
        return self.hint.__covariant__

    @property
    def contravariant(self) -> bool:
        return self.hint.__contravariant__

    @property
    def constraints(self) -> "Tuple[Any, ...]":
        return self.hint.__constraints__

    @property
    def bound(self) -> Any:
        return self.hint.__bound__
