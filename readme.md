# typeapi

[![Python](https://github.com/NiklasRosenstein/python-typeapi/actions/workflows/python.yml/badge.svg)](https://github.com/NiklasRosenstein/python-typeapi/actions/workflows/python.yml)

  [PEP484]: https://peps.python.org/pep-0484/
  [PEP585]: https://peps.python.org/pep-0585/
  [PEP604]: https://peps.python.org/pep-0604/

__Compatibility__: Python 3.6.3+

The `typeapi` package provides an object-oriented interface for introspecting [PEP484][] type hints at runtime,
including forward references that make use of the more recent [PEP585][] and [PEP604][] type hint features in
Python versions that don't natively support them.

The main API of this module is comprised of:

* `typeapi.TypeHint()` &ndash; A class to parse low-level type hints and present them in a consistent, object-oriented API.
* `typeapi.get_annotations()` &ndash; Retrieve an object's `__annotations__` with support for evaluating future type hints ([PEP585][], [PEP604][]).

The following kinds of type hints are currently supported:

| Concrete type | Description | Added in |
| ------------- | ----------- | -------- |
| `ClassTypeHint` | For any normal or generic type as well as `typing.Any`. Provides access to the underlying type, the type arguments and parameters, if any. | 1.0.0 |
| `UnionTypeHint` | Represents `Union` type hint and gives access to the union members. | 1.0.0 |
| `LiteralTypeHint` | Represents a `Literal` type hint and gives access to the literal values. | 1.0.0 |
| `AnnotatedTypeHint` | Represents an `Annotated` type hint and gives access to the annotated type as well as the metadata. | 1.0.0 |
| `TypeVarTypeHint` | Represents a `TypeVar` type hint and gives an interface to access the variable's metadata (such as constarints, variance, ...). | 1.0.0 |
| `ForwardRefTypeHint` | Represents a forward reference. Can be evaluated in Python 3.6+ even if it contains [PEP585][] and [PEP604][] expressions. | 1.0.0, future support in 1.3.0 |
| `TupleTypeHint` | Reperesents a `Tuple` type hint, allowing you to differentiate between repeated and explicitly sized tuples. | 1.2.0 |

## Examples

Inspect a `List[int]` type hint:

```py
# cat <<EOF | python -
from typeapi import ClassTypeHint, TypeHint
from typing import List

hint = TypeHint(List[int])
assert isinstance(hint, ClassTypeHint)
assert hint.type is list

item_hint = hint[0]
assert isinstance(item_hint, ClassTypeHint)
assert item_hint.type is int
```

Retrieve the metadata from an `Annotated[...]` type hint:

```py
# cat <<EOF | python -
from typeapi import AnnotatedTypeHint, ClassTypeHint, TypeHint
from typing_extensions import Annotated

hint = TypeHint(Annotated[int, 42])
assert isinstance(hint, AnnotatedTypeHint)
assert hint.type is int
assert hint.metadata == (42,)

sub_hint = hint[0]
assert isinstance(sub_hint, ClassTypeHint)
assert sub_hint.type is int
```

Parameterize one type hint with the parameterization of a generic alias:

```py
# cat <<EOF | python -
from dataclasses import dataclass
from typeapi import ClassTypeHint, TypeHint
from typing import Generic, TypeVar
from typing_extensions import Annotated

T = TypeVar("T")

@dataclass
class MyGeneric(Generic[T]):
  value: T

hint = TypeHint(MyGeneric[int])
assert isinstance(hint, ClassTypeHint)
assert hint.get_parameter_map() == {T: int}

member_hint = TypeHint(T).parameterize(hint.get_parameter_map())
assert isinstance(member_hint, ClassTypeHint)
assert member_hint.type is int
```

Evaluate forward references with `get_annotations()`:

```py
# cat <<EOF | python -
from typeapi import get_annotations
from typing import Optional
from sys import version_info

class MyType:
  a: "str | None"

annotations = get_annotations(MyType)

if version_info[:2] < (3, 10):
  assert annotations == {"a": Optional[str]}
else:
  assert annotations == {"a": str | None}
```

Evaluating forward references with the `TypeHint` API:

```py
# cat <<EOF | python -
from typeapi import ClassTypeHint, ForwardRefTypeHint, TypeHint

MyVector = "list[MyType]"

class MyType:
  pass

hint = TypeHint(MyVector).evaluate(globals())
print(hint)  # TypeHint(typing.List[__main__.MyType])
assert isinstance(hint, ClassTypeHint)
assert hint.type is list

item_hint = hint[0]
assert isinstance(item_hint, ClassTypeHint)
assert item_hint.type is MyType
```
