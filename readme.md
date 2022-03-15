# typeapi

Typeapi provides a stable and documented API to introspect Python `typing` type hints.

## Installation

    $ pip install typeapi

## Quickstart

```py
import typing
import typeapi

print(typeapi.of(typing.Any))                  # Type(object)
print(typeapi.of(typing.List))                 # Type(list)
print(typeapi.of(typing.Mapping[str, int]))    # Type(collections.abc.Mapping, (Type(str), Type(int)))
print(typeapi.of(typing.Union[str, int]))      # Union(int, str)
print(typeapi.of(str | int))                   # Union(int, str)
print(typeapi.of(str | int | None))            # Optional(Union[int, str])
print(typeapi.of(typing.Annotated[int, 42]))   # Annotated(int, 42)
print(typeapi.of(typing.Annotated[int, 42]))   # Annotated(int, 42)
print(typeapi.of('str', __name__))             # Type(str)
```
