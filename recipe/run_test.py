from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from subprocess import CompletedProcess, call, run
from textwrap import indent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

os.environ.update(
    PYTHONIOENCODING="utf-8",
    PYTHONLEGACYWINDOWSFSENCODING="utf-8",
)

from pytest import fixture

# env
VALE_NAME = os.environ["VALE_PKG_NAME"]
VALE_PATH = Path(sys.prefix) / "share/vale/styles"

# constants
PYTEST_ARGS = ["-svv", "--color=yes"]
VALE_INI = ".vale.ini"

# fixtures
NO_RULES_INI = """
MinAlertLevel = suggestion

[*]
BasedOnStyles = Vale
"""

INI_TEMPLATE = """
MinAlertLevel = suggestion
Packages = {name}

[*]
BasedOnStyles = {name}
"""

MD_WITH_AN_ISSUE = """
# hello world
"""

# output
EXPECT_JSON = """
  {
    "README.md": [
      {
        "Action": {
          "Name": "",
          "Params": null
        },
        "Suggestions": [],
        "Span": [
          3,
          13
        ],
        "Check": "Microsoft.Headings",
        "Description": "",
        "Link": "https://learn.microsoft.com/en-us/style-guide/capitalization",
        "Message": "'hello world' should use sentence-style capitalization.",
        "Severity": "suggestion",
        "Match": "hello world",
        "Line": 2
      }
    ]
  }
"""


def test_vale_path() -> None:
    res = _run_vale_json("ls-dirs")
    assert str(VALE_PATH) in res.stdout, f"`{VALE_PATH}` was not found"


def test_style_in_vale_path(a_markdown_file_with_issue: Path) -> None:
    ini = a_markdown_file_with_issue.parent / VALE_INI
    name = ini.parent.name
    style_dir = VALE_PATH / name
    assert style_dir.is_dir(), f"`{name}` is not in {VALE_PATH}"


def test_style_finds_or_fixes_issue(a_markdown_file_with_issue: Path) -> None:
    ini = a_markdown_file_with_issue.parent / VALE_INI
    name = ini.parent.name

    has_issues = _run_vale_json(a_markdown_file_with_issue.name)
    assert not has_issues.stderr, f"`{name}` didn't expect any stderr"
    assert json.loads(has_issues.stdout) == json.loads(EXPECT_JSON)

    ini.write_text(NO_RULES_INI, encoding="utf-8")

    no_issues = _run_vale_json(a_markdown_file_with_issue.name)
    assert not no_issues.stderr, f"didn't expect any stderr without `{name}`"
    assert not json.loads(no_issues.stdout)


@fixture
def in_a_project(tmp_path: Path) -> Iterator[Path]:
    project = tmp_path / VALE_NAME
    project.mkdir()
    old_cwd = Path.cwd()
    os.chdir(str(project))
    yield project
    os.chdir(old_cwd)


@fixture
def a_vale_ini(in_a_project: Path) -> Path:
    name = in_a_project.name
    ini = in_a_project / VALE_INI
    ini.write_text(INI_TEMPLATE.format(name=name), encoding="utf-8")
    print(name, "config")
    print(indent(ini.read_text(encoding="utf-8"), "\t"))
    return ini


@fixture
def a_markdown_file_with_issue(a_vale_ini: Path) -> Path:
    project = a_vale_ini.parent
    readme = project / "README.md"
    readme.write_text(MD_WITH_AN_ISSUE, encoding="utf-8")
    return readme


def _run_vale_json(*args: str) -> CompletedProcess[str]:
    args = ("vale", "--output=JSON", *args)
    print("\n>>>", *args)
    res = run(args, capture_output=True, check=False, encoding="utf-8")
    print("... rc", res.returncode)
    print("... stdout")
    print(indent(res.stdout, "\t"))
    print("... stderr")
    print(indent(res.stderr, "\t"), "\n")
    return res


if __name__ == "__main__":
    sys.exit(call([sys.executable, "-m", "pytest", *PYTEST_ARGS, __file__]))
