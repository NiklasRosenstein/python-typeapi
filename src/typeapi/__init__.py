
"""
The `typeapi` module provides a stable API to introspect Python #typing type hints.

Example:

```py
import typeapi, typing

hint = typeapi.of(typing.List[int])
assert hint == Type(list, nparams=1, parameters=None, args=(Type.of(int),))

hint = typeapi.of(int | str | None)
assert hint == typeapi.Union((Type.of(int), Type.of(str), Type.of(type(None))))
```

The #typeapi.of() function introspects the type hint passed as an argument and converts it to a stable description
using the dataclasses defined in #typeapi.model.
"""

__version__ = '0.1.5'

from .model import Hint, Type, Union, Annotated, ForwardRef, Any, ClassVar, Final, NoReturn, TypeGuard, Literal, \
    NewType, Unknown, eval_types, infuse_type_parameters, unwrap
from .parser import parse_type_hint as of
from .utils import get_annotations, get_type_hints, scope, scoped, type_repr

__all__ = [
  'Hint', 'Type', 'Union', 'Annotated', 'ForwardRef', 'Any', 'ClassVar', 'Final', 'NoReturn', 'TypeGuard', 'Literal',
  'NewType', 'Unknown', 'eval_types', 'infuse_type_parameters', 'unwrap',
  'of',
  'get_annotations', 'get_type_hints', 'scope', 'scoped', 'type_repr',
]
