# typeapi

This library provides a stable API to introspect Python's `typing` and `typing_extensions` type hints.

## Installation

    $ pip install typeapi

## Example

```py
import typing, typeapi
print(typeapi.of(typing.Mapping[typing.Annotated[str, "key"], typing.Literal[True, None, 'false']]))
# Type(collections.abc.Mapping, nparams=2, args=(Annotated(Type(str, nparams=0), 'key'), Literal(values=(True, None, 'false'))))
```
