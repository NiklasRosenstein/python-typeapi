# Supported Features

This page documents all features of the Python type annotation ecosystem that are supported by the `typeapi` package.

  [PEP484]: https://peps.python.org/pep-0484/
  [PEP526]: https://peps.python.org/pep-0526/
  [PEP585]: https://peps.python.org/pep-0585/
  [PEP586]: https://peps.python.org/pep-0586/
  [PEP593]: https://peps.python.org/pep-0593/
  [PEP604]: https://peps.python.org/pep-0604/
  [PEP646]: https://peps.python.org/pep-0646/
  [PEP695]: https://peps.python.org/pep-0695/

| Feature                              | Supported since | Example                              | Implemented via                                             | Related PEPs                                 |
|--------------------------------------|-----------------|--------------------------------------|-------------------------------------------------------------|----------------------------------------------|
| Normal type hint                     | 1.0.0           | `int`, `MyType`, `list[str]`         | [`ClassTypeHint`](./api/typeapi.md#typeapi.ClassTypeHint)           | [PEP484][], [PEP526][]                       |
| Generics in standard collection [^4] | 1.3.0           | `list[int]`, `dict[str, str]`        | [`ClassTypeHint`](./api/typeapi.md#typeapi.ClassTypeHint)           | [PEP585][]                                   |
| Tuples                               | 1.0.0           | `tuple[int, str]`, `Tuple[Any, ...]` | [`TupleTypeHint`](./api/typeapi.md#typeapi.TupleTypeHint)           | [PEP484][]                                   |
| Union types                          | 1.0.0           | `Union[int, str]`, `int \| str`      | [`UnionTypeHint`](./api/typeapi.md#typeapi.UnionTypeHint)           | [PEP484][], [PEP604][]                       |
| Sugar syntax for union types [^5]    | 1.3.0           | `int \| str`                         | [`UnionTypeHint`](./api/typeapi.md#typeapi.UnionTypeHint)           | [PEP604][]                                   |
| Literals                             | 1.0.0           | `Literal["a", 42]`                   | [`LiteralTypeHint`](./api/typeapi.md#typeapi.LiteralTypeHint)       | [PEP586][]                                   |
| Annotated                            | 1.0.0           | `Annotated[int, "hello_world"]`      | [`AnnotatedTypeHint`](./api/typeapi.md#typeapi.AnnotatedTypeHint)   | [PEP484][], [PEP593][]                       |
| Type variables                       | 1.0.0           | `TypeVar("T")`                       | [`TypeVarTypeHint`](./api/typeapi.md#typeapi.TypeVarTypeHint)       | [PEP484][], [PEP646][] [^2], [PEP695][] [^3] |
| Forward references                   | 1.0.0           | `"MyType"`                           | [`ForwardRefTypeHint`](./api/typeapi.md#typeapi.ForwardRefTypeHint) | [PEP484][]                                   |

[^2]: [PEP646 - Variadic Generics][PEP646] is not currently officially supported. Reflecting type hints using this
language feature may fail.

[^3]: [PEP695 - Type Parameter Syntax][PEP695] is not currently officially supported. Reflecting type hints using this
language feature may fail.

[^4]: Forward references may use the generic syntax introduced in [PEP585 - Type Hinting Generics In Standard Collections][PEP585]
in older Python (< 3.9) versions that do not implement this PEP. `typeapi` will evaluate the forward reference accordingly and
return the correct parameterized generic type hint from the `typing` module.

[^5]: The union syntax introduced by [PEP 604 - Allow writing union types as `X | Y`][PEP604] may be used in older Python
versions (< 3.10) via forward references. `typeapi` will evaluate the forward reference accordingly and return the corresponding
`typing.Union` type hint. Note that the evaluation of new-style union types from string literals will always return a
`typing.Union` despite the same syntax evaluated in Python versions supporting the syntax returning `types.UnionType`
instead.
