"""
Here we provide support to mock support of future type hint feature for older Python versions.
"""

import builtins
from typing import Any, Optional, Tuple, Union

from ..utils import HasGetitem, get_subscriptable_type_hint_from_origin


class FakeHint:
    """
    A placeholder for an actual type hint.
    """

    def __init__(self, origin: Any, args: Optional[Tuple["FakeHint", ...]] = None) -> None:
        self.origin = origin
        self.args = args

    def __or__(self, other: "FakeHint") -> "FakeHint":
        assert isinstance(other, FakeHint)
        if self.origin == Union:
            assert self.args is not None
            return FakeHint(Union, self.args + (other,))
        return FakeHint(Union, (self, other))

    def __getitem__(self, args: Union[Any, Tuple[Any, ...]]) -> "FakeHint":
        if self.args:
            raise RuntimeError(f"cannot subscript already subscripted type hint ({self})")
        if not isinstance(args, tuple):
            args = (args,)
        return FakeHint(self.origin, tuple(x if isinstance(x, FakeHint) else FakeHint(x) for x in args))

    def __getattr__(self, key: str) -> "FakeHint":
        return FakeHint(getattr(self.evaluate(), key))

    def evaluate(self) -> Any:
        if self.args is None:
            return self.origin
        else:
            return self.origin[tuple(x.evaluate() for x in self.args)]


class FakeProvider:
    def __init__(self, content: HasGetitem[str, Any]) -> None:
        self.content = content

    def __getitem__(self, key: str) -> FakeHint:
        try:
            value = self.content[key]
        except KeyError:
            value = vars(builtins)[key]
        return FakeHint(get_subscriptable_type_hint_from_origin(value))
