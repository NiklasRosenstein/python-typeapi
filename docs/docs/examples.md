# Examples

#### Inspect a `List[int]` type hint

```py
from typeapi import ClassTypeHint, TypeHint
from typing import List

hint = TypeHint(List[int])
assert isinstance(hint, ClassTypeHint)
assert hint.type is list

item_hint = hint[0]
assert isinstance(item_hint, ClassTypeHint)
assert item_hint.type is int
```

#### Retrieve the metadata from an `Annotated[...]` type hint

```py
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

#### Parameterize one type hint with the parameterization of a generic alias

```py
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

####  Evaluate forward references with `get_annotations()`

```py
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

####  Evaluating forward references with the `TypeHint` API

```py
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
