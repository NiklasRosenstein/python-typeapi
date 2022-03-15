
"""
The `typeapi` module provides a stable API to introspect Python #typing type hints.

Example:

```py
import typeapi, typing

hint = typeapi.of(typing.List[int])
assert hint == typeapi.Type(list, nparams=1, parameters=None, args=(int,))

hint = typeapi.of(int | str | None)
assert hint == typeapi.Union((int, str, type(None)))
```

The #typeapi.of() function introspects the type hint passed as an argument and converts it to a stable description
using the dataclasses defined in #typeapi.model.
"""

__version__ = '0.1.0a3'

from .model import Hint, Type, Union, Annotated, ForwardRef, Any, ClassVar, Final, NoReturn, TypeGuard, Literal, NewType, Unknown
from .parser import parse_type_hint as of

__all__ = [
  'Hint', 'Type', 'Union', 'Annotated', 'ForwardRef', 'Any', 'ClassVar', 'Final', 'NoReturn', 'TypeGuard', 'Literal', 'NewType', 'Unknown',
  'TypeInfo',
  'of',
]
