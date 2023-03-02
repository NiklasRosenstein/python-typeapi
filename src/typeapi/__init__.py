__version__ = "1.4.0"

from .typehint import (
    AnnotatedTypeHint,
    ClassTypeHint,
    ForwardRefTypeHint,
    LiteralTypeHint,
    TupleTypeHint,
    TypeHint,
    TypeVarTypeHint,
    UnionTypeHint,
)
from .utils import TypedDictProtocol, get_annotations, is_typed_dict, type_repr

__all__ = [
    # .typehint
    "AnnotatedTypeHint",
    "ClassTypeHint",
    "ForwardRefTypeHint",
    "LiteralTypeHint",
    "TupleTypeHint",
    "TypeHint",
    "TypeVarTypeHint",
    "UnionTypeHint",
    # .utils
    "get_annotations",
    "is_typed_dict",
    "type_repr",
    "TypedDictProtocol",
]
