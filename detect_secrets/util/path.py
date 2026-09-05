# detect-secrets-plus: modified from upstream Yelp/detect-secrets (Apache-2.0). See NOTICE.
import os
import re
from pathlib import Path
from typing import Literal
from typing import Optional
from typing import Tuple

CustomPathKind = Literal["module", "file", "invalid"]


class CustomPath:
    def __init__(
        self,
        kind: CustomPathKind = "invalid",
        module_path: Optional[str] = None,
        file_path: Optional[str] = None,
        function_name: Optional[str] = None,
    ) -> None:
        self.kind = kind
        self.module_path = module_path
        self.file_path = file_path
        self.function_name = function_name

    def __repr__(self) -> str:
        return (
            f"CustomPath(kind={self.kind!r}, "
            f"module_path={self.module_path!r}, "
            f"file_path={self.file_path!r}, "
            f"function_name={self.function_name!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CustomPath):
            return NotImplemented
        return (
            self.kind == other.kind
            and self.module_path == other.module_path
            and self.file_path == other.file_path
            and self.function_name == other.function_name
        )


_DRIVE_AFTER_SLASH = re.compile(r"^/[A-Za-z]:[\\/]")


def _strip_file_scheme(path: str) -> Tuple[str, bool]:
    if path.startswith("file:///"):
        return "/" + path[len("file:///") :], True
    if path.startswith("file://"):
        return path[len("file://") :], True
    return path, False


def parse_path(path: str) -> CustomPath:
    remainder, had_file_scheme = _strip_file_scheme(path)

    if not had_file_scheme and "://" in remainder:
        return CustomPath()

    if "::" in remainder:
        file_part, _, function_name = remainder.partition("::")

        if not function_name or not function_name.isidentifier():
            return CustomPath()

        file_part = _normalize_file_part(file_part, had_file_scheme)
        return CustomPath(
            kind="file",
            file_path=file_part,
            function_name=function_name,
        )

    if had_file_scheme:
        remainder = _normalize_file_part(remainder, had_file_scheme)
        return CustomPath(
            kind="file",
            file_path=remainder,
            function_name=None,
        )

    return CustomPath(
        kind="module",
        module_path=path,
    )


def _normalize_file_part(file_part: str, had_file_scheme: bool) -> str:
    if had_file_scheme:
        match = _DRIVE_AFTER_SLASH.match(file_part)
        if match:
            file_part = file_part[1:]
    return file_part


def get_relative_path(root: str, path: str) -> Optional[str]:
    if Path(os.getcwd()) == Path(root):
        return get_relative_path_if_in_cwd(path)

    full_path = os.path.realpath(path)
    full_root = os.path.realpath(root)
    try:
        return os.path.relpath(full_path, full_root)
    except ValueError:
        return None


def get_relative_path_if_in_cwd(path: str) -> Optional[str]:
    filepath = os.path.realpath(path)
    cwd = os.getcwd()
    try:
        rel = os.path.relpath(filepath, cwd)
        if rel == ".":
            rel = os.path.basename(filepath)
    except ValueError:
        return None

    if os.path.isfile(os.path.join(cwd, rel)):
        return rel

    return None


def convert_local_os_path(path: str) -> str:
    scheme_prefix = ""
    remainder = path
    if path.startswith("file://"):
        scheme_prefix = "file://"
        remainder = path[len("file://") :]

    if os.sep == "/":
        remainder = remainder.replace("\\", "/")
    else:
        remainder = remainder.replace("/", "\\")

    return scheme_prefix + remainder
