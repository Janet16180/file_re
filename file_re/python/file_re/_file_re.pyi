from typing import Dict, List, Optional

class Match:
    groups: List[Optional[str]]
    named_groups: Dict[str, Optional[str]]
    start: int
    end: int
    match_str: str

class MatchIter:
    def __iter__(self) -> "MatchIter": ...
    def __next__(self) -> Match: ...

class Pattern:
    pattern: str
    flags: int
    def __init__(self, pattern: str, flags: int = 0) -> None: ...
    def search(
        self, file_path: str, max_span_lines: Optional[int] = None
    ) -> Optional[Match]: ...
    def match(
        self, file_path: str, max_span_lines: Optional[int] = None
    ) -> Optional[Match]: ...
    def findall(
        self, file_path: str, max_span_lines: Optional[int] = None
    ) -> List[List[Optional[str]]]: ...
    def finditer(
        self, file_path: str, max_span_lines: Optional[int] = None
    ) -> MatchIter: ...
    def __repr__(self) -> str: ...

def _search(
    regex: str,
    file_path: str,
    flags: int = 0,
    *,
    max_span_lines: Optional[int] = None,
) -> Optional[Match]: ...
def _match(
    regex: str,
    file_path: str,
    flags: int = 0,
    *,
    max_span_lines: Optional[int] = None,
) -> Optional[Match]: ...
def _findall(
    regex: str,
    file_path: str,
    flags: int = 0,
    *,
    max_span_lines: Optional[int] = None,
) -> List[List[Optional[str]]]: ...
def _finditer(
    regex: str,
    file_path: str,
    flags: int = 0,
    *,
    max_span_lines: Optional[int] = None,
) -> MatchIter: ...
