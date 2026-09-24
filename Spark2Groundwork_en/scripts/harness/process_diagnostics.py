"""Conservative Python crash classification shared by the runner and buttons.

This recognises interpreter diagnostics, not arbitrary exception words in findings.
It is a diagnostic heuristic, not proof of process success or tool authenticity.
"""
from __future__ import annotations
import re

_FILE_LINE = re.compile(r'^  File ".*", line [0-9]+(?:, in .*)?$')
_PARSE_ERROR = re.compile(r'^(?:SyntaxError|IndentationError|TabError):(?: |$)')

def is_python_crash(returncode: int, stderr: str | None) -> bool:
    if returncode == 0:
        return False
    lines = (stderr or "").splitlines()
    if "Traceback (most recent call last):" in lines:
        return True
    # Parse failures have no traceback header. Require both the file diagnostic
    # and the terminal exception line, in order. Quoted tokens alone are findings.
    return any(_PARSE_ERROR.match(line) and
               any(_FILE_LINE.match(previous) for previous in lines[:i])
               for i, line in enumerate(lines))
