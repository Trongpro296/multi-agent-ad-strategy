"""Reserved execution-failure markers, with compatibility for saved workflows."""

EXEC_FAILURE = "[[EXEC_FAIL]]"
LEGACY_EXEC_FAILURE = "==CODE EXECUTION FAILED=="
EXEC_FAILURE_MARKERS = (EXEC_FAILURE, LEGACY_EXEC_FAILURE)


def has_execution_failure(text: str) -> bool:
    return any(marker in (text or "") for marker in EXEC_FAILURE_MARKERS)


def execution_marker_aliases(keyword: str, *, case_sensitive: bool = True) -> tuple[str, ...]:
    """Only these two exact reserved keywords are aliases; FAIL is ordinary text."""
    markers = EXEC_FAILURE_MARKERS if case_sensitive else tuple(m.lower() for m in EXEC_FAILURE_MARKERS)
    term = keyword if case_sensitive else keyword.lower()
    return markers if term in markers else (term,)
