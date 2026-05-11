from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED_PREFIXES = ("Merge ", "Revert ", "fixup! ", "squash! ")
CONVENTIONAL_SUBJECT = re.compile(
    r"^(build|chore|ci|docs|feat|fix|perf|refactor|style|test)"
    r"(\([a-z0-9][a-z0-9-]*\))?!?: .{1,72}$"
)


def is_valid_subject(subject: str) -> bool:
    if subject.startswith(ALLOWED_PREFIXES):
        return True
    return CONVENTIONAL_SUBJECT.fullmatch(subject) is not None


def read_subject(path: Path) -> str:
    with path.open(encoding="utf-8") as commit_msg:
        return commit_msg.readline().strip()


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Usage: check_commit_msg.py <commit-msg-file>", file=sys.stderr)
        return 2

    subject = read_subject(Path(args[0]))
    if is_valid_subject(subject):
        return 0

    print(
        "Commit subject must use Conventional Commits, for example:\n"
        "  feat(supplier-matching): add catalog filter\n"
        "Allowed types: build, chore, ci, docs, feat, fix, perf, refactor, style, test",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
