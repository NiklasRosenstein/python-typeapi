# typeapi

Typeapi provides a sane and stable API to introspect Python type hints.

## Installation

    $ pip install typeapi

## Quickstart

```py
import typing
from typeapi import parse_type_hint

print(parse_type_hint(typing.Any))                  # Type(object)
print(parse_type_hint(typing.List))                 # Type(list)
print(parse_type_hint(typing.Mapping[str, int]))    # Type(collections.abc.Mapping, (Type(str), Type(int)))
print(parse_type_hint(typing.Union[str, int]))      # Union(int, str)
print(parse_type_hint(str | int))                   # Union(int, str)
print(parse_type_hint(str | int | None))            # Optional(Union[int, str])
print(parse_type_hint(typing.Annotated[int, 42]))   # Annotated(int, 42)
print(parse_type_hint(typing.Annotated[int, 42]))   # Annotated(int, 42)
print(parse_type_hint('str', __name__))             # Type(str)
```
