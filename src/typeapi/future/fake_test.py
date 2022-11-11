from typing import List, Optional, Union

import pytest

from typeapi.future.fake import FakeHint


def test__FakeHint__evaluate() -> None:
    assert FakeHint(int).evaluate() is int
    assert FakeHint(Union, (FakeHint(int), FakeHint(str))).evaluate() == Union[int, str]


def test__FakeHint__union() -> None:
    assert (FakeHint(int) | FakeHint(str)).evaluate() == Union[int, str]
    assert ((FakeHint(int) | FakeHint(str)) | FakeHint(float)).evaluate() == Union[int, str, float]
    assert (FakeHint(int) | FakeHint(None)).evaluate() == Optional[int]


def test__FakeHint__subscript() -> None:
    assert FakeHint(Union)[FakeHint(int), FakeHint(str)].evaluate() == Union[int, str]
    assert FakeHint(List)[FakeHint(int)].evaluate() == List[int]

    with pytest.raises(TypeError) as excinfo:
        FakeHint(int)[FakeHint(str)].evaluate()
    assert "is not subscriptable" in str(excinfo.value)


def test__FakeHint__getattr() -> None:
    import typing

    assert FakeHint(typing).Union.evaluate() == Union
    assert FakeHint(typing).Union.evaluate() == Union
    assert FakeHint(typing).List[FakeHint(int)].evaluate() == List[int]
