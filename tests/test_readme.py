import collections.abc

import typing_extensions as te

from typeapi import Annotated, Literal, Type


def test_readme_example():
    import typing

    import typeapi

    value = typeapi.of(typing.Mapping[te.Annotated[str, "key"], te.Literal[True, None, "false"]])
    assert value == Type(
        collections.abc.Mapping,
        nparams=2,
        args=(Annotated(Type(str, nparams=0), ("key",)), Literal(values=(True, None, "false"))),
    )
