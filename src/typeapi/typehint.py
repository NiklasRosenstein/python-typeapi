import abc
from typing import Any, Dict, Generic, Iterator, List, Mapping, Tuple, TypeVar, Union, cast, overload

from typing_extensions import Annotated

from .utils import (
    IS_PYTHON_AT_LAST_3_6,
    IS_PYTHON_AT_LAST_3_8,
    ForwardRef,
    HasGetitem,
    get_subscriptable_type_hint_from_origin,
    get_type_hint_args,
    get_type_hint_origin_or_none,
    get_type_hint_original_bases,
    get_type_hint_parameters,
    type_repr,
)

NoneType = type(None)


class _TypeHintMeta(abc.ABCMeta):
    """
    Meta class for :class:`TypeHint` to cache created instances and correctly
    instantiate the appropriate implementation based on the low-level type
    hint.
    """

    # _cache: Dict[str, "TypeHint"] = {}

    def __call__(cls, hint: object) -> "TypeHint":  # type: ignore[override]
        # If the current class is not the base "TypeHint" class, we should let
        # object construction continue as usual.
        if cls is not TypeHint:
            return super().__call__(hint)  # type: ignore[no-any-return]
        # Otherwise, we are in this "TypeHint" class.

        # If the hint is a type hint in itself, we can return it as-is.
        if isinstance(hint, TypeHint):
            return hint

        # TODO(NiklasRosenstein): Implement a caching method that does not rely
        #       on the type name (there can be multiple definitions of a type
        #       with the same name but they are still distinct types; for example
        #       when defining a type in a function body).
        # # Check if the hint is already cached.
        # hint_key = str(hint)
        # if hint_key in cls._cache:
        #     return cls._cache[hint_key]

        # Create the wrapper for the low-level type hint.
        wrapper = cls._make_wrapper(hint)
        # cls._cache[hint_key] = wrapper
        return wrapper

    def _make_wrapper(cls, hint: object) -> "TypeHint":
        """
        Create the :class:`TypeHint` implementation that wraps the given
        low-level type hint.
        """

        if hint is None:
            hint = NoneType

        if isinstance(hint, (ForwardRef, str)):
            return ForwardRefTypeHint(hint)

        origin = get_type_hint_origin_or_none(hint)
        if origin == Union:
            return UnionTypeHint(hint)
        elif str(origin).endswith(".Literal"):
            return LiteralTypeHint(hint)
        elif ".Annotated" in str(origin):
            return AnnotatedTypeHint(hint)
        elif isinstance(hint, TypeVar):
            return TypeVarTypeHint(hint)
        elif origin == tuple or hint == tuple:
            return TupleTypeHint(hint)

        return ClassTypeHint(hint)


# NOTE(NiklasRosenstein): We inherit from object to workaround
#       https://github.com/NiklasRosenstein/pydoc-markdown/issues/272.


class TypeHint(object, metaclass=_TypeHintMeta):
    """
    Base class that provides an object-oriented interface to a Python type hint.
    """

    def __init__(self, hint: object) -> None:
        self._hint = hint
        self._origin = get_type_hint_origin_or_none(hint)
        self._args = get_type_hint_args(hint)
        self._parameters = get_type_hint_parameters(hint)

    def __repr__(self) -> str:
        return f"TypeHint({type_repr(self._hint)})"

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

    def __iter__(self) -> Iterator["TypeHint"]:
        for i in range(len(self.args)):
            yield self[i]

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
            try:
                return TypeHint(self.args[index])
            except IndexError:
                raise IndexError(f"TypeHint index {index} out of range [0..{len(self.args)}[")
        else:
            return [TypeHint(x) for x in self.args[index]]

    def _copy_with_args(self, args: "Tuple[Any, ...]") -> "TypeHint":
        """
        Internal. Create a copy of this type hint with updated type arguments.
        """

        generic = get_subscriptable_type_hint_from_origin(self.origin)
        try:
            new_hint = generic[args]
        except TypeError as exc:
            raise TypeError(f"{type_repr(generic)}: {exc}")
        return TypeHint(new_hint)

    def parameterize(self, parameter_map: Mapping[object, Any]) -> "TypeHint":
        """
        Replace references to the type variables in the keys of *parameter_map*
        with the type hints of the associated values.

        :param parameter_map: A dictionary that maps :class:`TypeVar` to other
            type hints.
        """

        if self.origin is not None and self.args:
            args = tuple(TypeHint(x).parameterize(parameter_map).hint for x in self.args)
            return self._copy_with_args(args)
        else:
            return self

    def evaluate(self, context: HasGetitem[str, Any]) -> "TypeHint":
        if self.origin is not None and self.args:
            args = tuple(TypeHint(x).evaluate(context).hint for x in self.args)
            return self._copy_with_args(args)
        else:
            return self


class ClassTypeHint(TypeHint):
    def __init__(self, hint: object) -> None:
        super().__init__(hint)
        assert isinstance(self.hint, type) or isinstance(self.origin, type), (
            "ClassTypeHint must be initialized from a real type or a generic that points to a real type. "
            f'Got "{self.hint!r}" with origin "{self.origin}"'
        )

    def parameterize(self, parameter_map: Mapping[object, Any]) -> "TypeHint":
        if self.type is Generic:  # type: ignore[comparison-overlap]
            return self
        return super().parameterize(parameter_map)

    @property
    def type(self) -> type:
        if isinstance(self.origin, type):
            return self.origin
        if isinstance(self.hint, type):
            return self.hint
        assert False, "ClassTypeHint not initialized from a real type or a generic that points to a real type."

    @property
    def bases(self) -> "Tuple[Any, ...] | None":
        return get_type_hint_original_bases(self.type)

    def get_parameter_map(self) -> Dict[Any, Any]:
        if not self.args:
            return {}
        return dict(zip(TypeHint(self.type).parameters, self.args))


class UnionTypeHint(TypeHint):
    def has_none_type(self) -> bool:
        return NoneType in self._args

    def without_none_type(self) -> TypeHint:
        args = tuple(x for x in self._args if x is not NoneType)
        if len(args) == 1:
            return TypeHint(args[0])
        else:
            return self._copy_with_args(args)


class LiteralTypeHint(TypeHint):
    @property
    def args(self) -> Tuple[Any, ...]:
        return ()

    def parameterize(self, parameter_map: Mapping[object, Any]) -> "TypeHint":
        return self

    def __len__(self) -> int:
        return 0

    @property
    def values(self) -> Tuple[Any, ...]:
        return self._args


class AnnotatedTypeHint(TypeHint):
    @property
    def args(self) -> Tuple[Any, ...]:
        return (self._args[0],)

    def _copy_with_args(self, args: "Tuple[Any, ...]") -> "TypeHint":
        assert len(args) == 1
        new_hint = Annotated[args + (self._args[1:])]  # type: ignore
        return AnnotatedTypeHint(new_hint)

    def __len__(self) -> int:
        return 1

    @property
    def type(self) -> Any:
        return self._args[0]

    @property
    def metadata(self) -> Tuple[Any, ...]:
        return self._args[1:]


class TypeVarTypeHint(TypeHint):
    @property
    def hint(self) -> TypeVar:
        assert isinstance(self._hint, TypeVar)
        return self._hint

    def parameterize(self, parameter_map: Mapping[object, Any]) -> "TypeHint":
        return TypeHint(parameter_map.get(self.hint, self.hint))

    def evaluate(self, context: HasGetitem[str, Any]) -> TypeHint:
        return self

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


class ForwardRefTypeHint(TypeHint):
    def __init__(self, hint: object) -> None:
        super().__init__(hint)
        if isinstance(self._hint, str):
            self._forward_ref = ForwardRef(self._hint)
        elif isinstance(self._hint, ForwardRef):
            self._forward_ref = self._hint
        else:
            raise TypeError(
                f"ForwardRefTypeHint must be initialized from a typing.ForwardRef or str. Got: {type(self._hint)!r}"
            )

    def parameterize(self, parameter_map: Mapping[object, Any]) -> TypeHint:
        raise RuntimeError(
            "ForwardRef cannot be parameterized. Ensure that your type hint is fully "
            "evaluated before parameterization."
        )

    def evaluate(self, context: HasGetitem[str, Any]) -> TypeHint:
        retyped_context = cast(Mapping[str, Any], context)

        if IS_PYTHON_AT_LAST_3_6:
            hint = eval(self.expr, {}, retyped_context)
        elif IS_PYTHON_AT_LAST_3_8:
            # Mypy doesn't know about the third arg
            hint = self.ref._evaluate({}, retyped_context)  # type: ignore[arg-type]
        else:
            hint = self.ref._evaluate({}, retyped_context, set())  # type: ignore[arg-type,call-arg]
        return TypeHint(hint).evaluate(context)

    @property
    def hint(self) -> "ForwardRef | str":
        return self._hint  # type: ignore

    @property
    def ref(self) -> ForwardRef:
        return self._forward_ref

    @property
    def expr(self) -> str:
        return self._forward_ref.__forward_arg__


class TupleTypeHint(TypeHint):
    def __init__(self, hint: object) -> None:
        super().__init__(hint)
        if self._args == ((),):
            self._args = ()
        elif self._args == () and self._hint == tuple:
            self._args = (Any, ...)
            self._origin = tuple
        if ... in self._args:
            assert self._args[-1] == ..., "Tuple Ellipsis not as last arg"
            assert len(self._args) == 2, "Tuple with Ellipsis has more than two args"
            self._repeated = True
            self._args = self._args[:-1]
        else:
            self._repeated = False

    def _copy_with_args(self, args: "Tuple[Any, ...]") -> "TypeHint":
        if self._repeated:
            args = args + (...,)
        return super()._copy_with_args(args)

    @property
    def repeated(self) -> bool:
        """
        Returns `True` if the Tuple is of arbitrary length, but only of one type.
        """

        return self._repeated
