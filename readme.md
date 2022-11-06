# typeapi

[![Python](https://github.com/NiklasRosenstein/python-typeapi/actions/workflows/python.yml/badge.svg)](https://github.com/NiklasRosenstein/python-typeapi/actions/workflows/python.yml)

__Compatibility__: Python 3.6+

The `typeapi` package provides an object-oriented interface for introspecting type hints from the `typing` and
`typing_extensions` module at runtime. Currently, only a subset of the different kinds of type hints are supported,
namely through the following representations:

| Concrete type | Description |
| ------------- | ----------- |
| `ClassTypeHint` | For any normal or generic type as well as `typing.Any`. Provides access to the underlying type, the type arguments and parameters, if any. |
| `UnionTypeHint` | Represents `Union` type hint and gives access to the union members. |
| `LiteralTypeHint` | Represents a `Literal` type hint and gives access to the literal values. |
| `AnnotatedTypeHint` | Represents an `Annotated` type hint and gives access to the annotated type as well as the metadata. |
| `TypeVarTypeHint` | Represents a `TypeVar` type hint and gives an interface to access the variable's metadata (such as constarints, variance, ...). |

All type hints representations are constructed by calling the `TypeHint()` constructor and passing the low-level type hint.

```py
from typeapi import TypeHint, ClassTypeHint
from typing import List

hint = TypeHint(List[int])
assert isinstance(hint, ClassTypeHint)
assert hint.type == list

item_hint = hint[0]
assert isinstance(item_hint, ClassType)
assert item_hint.type == int
```

## Planned work

* Support more features of the typing system (e.g. `ClassVar`, `ParamSpec`, ...)
* Support evaluating forward references that utilize newer Python language features (such as built-in type subscripts
  and type union syntax).
    * Subscript support could be achieved by mocking the built-in types during the evaluation of the expression.
    * Type unions could be achieved by rewriting the expression AST before evaluating and mocking every value in the expression.
