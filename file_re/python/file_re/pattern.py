from pathlib import Path
from typing import Any, Iterator, List, Optional, Tuple, Union

from ._file_re import Pattern as _RustPattern
from .match import Match

_PathLike = Union[str, Path]


def _validate_span_lines(max_span_lines: Optional[int]) -> None:
    if max_span_lines is not None and max_span_lines <= 0:
        raise ValueError("max_span_lines must be >= 1")


def _to_str_path(file_path: _PathLike) -> str:
    if isinstance(file_path, Path):
        return str(file_path)
    return file_path


def _wrap_match(result: Any) -> Optional[Match]:
    if result is None:
        return None
    return Match(
        match_str=result.match_str,
        start=result.start,
        end=result.end,
        matchs_list=result.groups,
        matchs_dict=result.named_groups,
    )


def _post_process_findall(
    match_list: List[List[Optional[str]]],
) -> Union[List[Optional[str]], List[Tuple[Optional[str], ...]]]:
    if not match_list:
        return match_list
    if len(match_list[0]) == 1:
        return [item for sublist in match_list for item in sublist]
    return [tuple(sublist[1:]) for sublist in match_list]


class _MatchIterator:
    """
    Adapter that converts Rust ``_file_re.MatchIter`` outputs into Python
    :class:`Match` objects. Iteration is lazy; the underlying file handle
    is held open by the Rust iterator until exhaustion or garbage collection.
    """

    def __init__(self, rust_iter: Any) -> None:
        self._iter = rust_iter

    def __iter__(self) -> "_MatchIterator":
        return self

    def __next__(self) -> Match:
        result = next(self._iter)
        wrapped = _wrap_match(result)
        assert wrapped is not None
        return wrapped


class Pattern:
    """
    A compiled regex pattern, mirroring :class:`re.Pattern`.

    Instances are produced by :func:`file_re.compile` and hold a compiled
    Rust regex. The compiled pattern is reused across calls, avoiding
    recompilation overhead for patterns applied to multiple files.

    Parameters
    ----------
    pattern : str
        The regex source string.
    flags : int, optional
        Bitwise OR of :mod:`re` flags. Defaults to ``0``.

    Raises
    ------
    ValueError
        If ``pattern`` is not a valid regex, or if ``flags`` contains
        :data:`re.LOCALE`.
    """

    def __init__(self, pattern: str, flags: int = 0) -> None:
        self._rust_pattern = _RustPattern(pattern, flags)
        self._pattern = pattern
        self._flags = flags

    @property
    def pattern(self) -> str:
        """
        The regex source string used to compile this pattern.

        Returns
        -------
        str
            The original pattern string.
        """
        return self._pattern

    @property
    def flags(self) -> int:
        """
        The flags used to compile this pattern.

        Returns
        -------
        int
            Bitwise OR of the :mod:`re` flags supplied at compile time.
        """
        return self._flags

    def search(
        self,
        file_path: _PathLike,
        max_span_lines: Optional[int] = None,
    ) -> Optional[Match]:
        """
        Scan the file and return the first match anywhere.

        Parameters
        ----------
        file_path : str or pathlib.Path
            Path to the target file. Gzip (``.gz``) and xz (``.xz``)
            archives are decoded transparently.
        max_span_lines : int or None, optional
            Controls how much of the file is held in memory.
            ``None`` (default) loads the whole file; ``1`` scans line by
            line; ``N > 1`` uses a sliding ``N``-line window.

        Returns
        -------
        Match or None
            The first match, or ``None`` if no match is found.

        Raises
        ------
        ValueError
            If ``max_span_lines`` is provided and not ``>= 1``.
        OSError
            If the file cannot be opened or read.
        """
        _validate_span_lines(max_span_lines)
        return _wrap_match(
            self._rust_pattern.search(_to_str_path(file_path), max_span_lines)
        )

    def match(
        self,
        file_path: _PathLike,
        max_span_lines: Optional[int] = None,
    ) -> Optional[Match]:
        """
        Match the pattern anchored at the start of the file.

        Parameters
        ----------
        file_path : str or pathlib.Path
            Path to the target file.
        max_span_lines : int or None, optional
            See :meth:`search`.

        Returns
        -------
        Match or None
            The match, or ``None`` if the pattern does not match at
            position 0.

        Raises
        ------
        ValueError
            If ``max_span_lines`` is provided and not ``>= 1``.
        OSError
            If the file cannot be opened or read.
        """
        _validate_span_lines(max_span_lines)
        return _wrap_match(
            self._rust_pattern.match(_to_str_path(file_path), max_span_lines)
        )

    def findall(
        self,
        file_path: _PathLike,
        max_span_lines: Optional[int] = None,
    ) -> Union[List[Optional[str]], List[Tuple[Optional[str], ...]]]:
        """
        Return all non-overlapping matches in the file.

        Parameters
        ----------
        file_path : str or pathlib.Path
            Path to the target file.
        max_span_lines : int or None, optional
            See :meth:`search`.

        Returns
        -------
        list
            If the pattern has no capturing groups, a list of match
            strings. Otherwise, a list of tuples containing the captured
            groups (non-participating groups are ``None``).

        Raises
        ------
        ValueError
            If ``max_span_lines`` is provided and not ``>= 1``.
        OSError
            If the file cannot be opened or read.
        """
        _validate_span_lines(max_span_lines)
        return _post_process_findall(
            self._rust_pattern.findall(_to_str_path(file_path), max_span_lines)
        )

    def finditer(
        self,
        file_path: _PathLike,
        max_span_lines: Optional[int] = None,
    ) -> Iterator[Match]:
        """
        Iterate lazily over all non-overlapping matches in the file.

        Parameters
        ----------
        file_path : str or pathlib.Path
            Path to the target file.
        max_span_lines : int or None, optional
            See :meth:`search`.

        Returns
        -------
        Iterator of Match
            A lazy iterator that yields :class:`Match` objects. The
            underlying file is closed when the iterator is exhausted or
            garbage collected.

        Raises
        ------
        ValueError
            If ``max_span_lines`` is provided and not ``>= 1``.
        OSError
            If the file cannot be opened.
        """
        _validate_span_lines(max_span_lines)
        return _MatchIterator(
            self._rust_pattern.finditer(_to_str_path(file_path), max_span_lines)
        )

    def __repr__(self) -> str:
        return f"Pattern(pattern={self._pattern!r}, flags={self._flags})"
