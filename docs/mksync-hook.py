import os
import typing as t
from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig  # type: ignore
from mkdocs.structure.pages import Page  # type: ignore
from mksync import mksync_file  # type: ignore


def on_page_read_source(page: Page, config: MkDocsConfig) -> str:
    path = Path(page.file.abs_src_path)
    cwd = os.getcwd()
    os.chdir(path.parent)
    try:
        result = mksync_file(path)
    finally:
        os.chdir(cwd)
    return t.cast(str, result.content)
