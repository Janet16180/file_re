import re
import warnings
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union

from ._file_re import _findall, _finditer, _match, _search
from .match import Match
from .pattern import (
    Pattern,
    _MatchIterator,
    _PathLike,
    _post_process_findall,
    _to_str_path,
    _validate_span_lines,
    _wrap_match,
)

_ASCII_WARNED = False


def _check_flags(flags: int) -> None:
    global _ASCII_WARNED
    if flags & re.DEBUG:
        warnings.warn(
            "re.DEBUG is not supported by file_re and is ignored.",
            UserWarning,
            stacklevel=3,
        )
    if flags & re.ASCII and not _ASCII_WARNED:
        warnings.warn(
            "re.ASCII in file_re disables Unicode character class matching entirely "
            "(Rust regex semantics); this is broader than Python's re.ASCII.",
            UserWarning,
            stacklevel=3,
        )
        _ASCII_WARNED = True


class file_re_cls:
    """
    Static facade that exposes the public ``file_re`` API.

    The class mirrors the module-level surface of :mod:`re`. Each method
    is a thin adapter over the Rust extension: it coerces ``Path`` inputs,
    validates ``max_span_lines``, emits warnings for flags that diverge
    from :mod:`re`, and wraps results in Python :class:`Match` objects.
    """

    @staticmethod
    def search(
        pattern: str,
        file_path: _PathLike,
        flags: int = 0,
        *,
        max_span_lines: Optional[int] = None,
    ) -> Optional[Match]:
        """
        Scan the file and return the first match anywhere.

        Parameters
        ----------
        pattern : str
            The regex pattern to search for.
        file_path : str or pathlib.Path
            Path to the file. ``.gz`` and ``.xz`` archives are decoded
            transparently.
        flags : int, optional
            Bitwise OR of :mod:`re` flags. Defaults to ``0``.
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
            If ``max_span_lines`` is provided and not ``>= 1``, if
            ``pattern`` is invalid, or if ``flags`` contains
            :data:`re.LOCALE`.
        OSError
            If the file cannot be opened or read.

        Examples
        --------
        >>> from file_re import file_re
        >>> m = file_re.search(r"ERROR: (\\w+)", "server.log")
        >>> m.group(1) if m else None
        """
        _validate_span_lines(max_span_lines)
        _check_flags(flags)
        return _wrap_match(
            _search(pattern, _to_str_path(file_path), flags, max_span_lines=max_span_lines)
        )

    @staticmethod
    def match(
        pattern: str,
        file_path: _PathLike,
        flags: int = 0,
        *,
        max_span_lines: Optional[int] = None,
    ) -> Optional[Match]:
        """
        Match the pattern anchored at the start of the file.

        Parameters
        ----------
        pattern : str
            The regex pattern to match.
        file_path : str or pathlib.Path
            Path to the file.
        flags : int, optional
            Bitwise OR of :mod:`re` flags. Defaults to ``0``.
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
            If ``max_span_lines`` is not ``>= 1``, if ``pattern`` is
            invalid, or if ``flags`` contains :data:`re.LOCALE`.
        OSError
            If the file cannot be opened or read.
        """
        _validate_span_lines(max_span_lines)
        _check_flags(flags)
        return _wrap_match(
            _match(pattern, _to_str_path(file_path), flags, max_span_lines=max_span_lines)
        )

    @staticmethod
    def findall(
        pattern: str,
        file_path: _PathLike,
        flags: int = 0,
        *,
        max_span_lines: Optional[int] = None,
    ) -> Union[List[Optional[str]], List[Tuple[Optional[str], ...]]]:
        """
        Return all non-overlapping matches in the file.

        Parameters
        ----------
        pattern : str
            The regex pattern to search for.
        file_path : str or pathlib.Path
            Path to the file.
        flags : int, optional
            Bitwise OR of :mod:`re` flags. Defaults to ``0``.
        max_span_lines : int or None, optional
            See :meth:`search`.

        Returns
        -------
        list
            If ``pattern`` has no capturing groups, a list of match
            strings. Otherwise, a list of tuples containing the captured
            groups (non-participating groups are ``None``).

        Raises
        ------
        ValueError
            If ``max_span_lines`` is not ``>= 1``, if ``pattern`` is
            invalid, or if ``flags`` contains :data:`re.LOCALE`.
        OSError
            If the file cannot be opened or read.
        """
        _validate_span_lines(max_span_lines)
        _check_flags(flags)
        return _post_process_findall(
            _findall(pattern, _to_str_path(file_path), flags, max_span_lines=max_span_lines)
        )

    @staticmethod
    def finditer(
        pattern: str,
        file_path: _PathLike,
        flags: int = 0,
        *,
        max_span_lines: Optional[int] = None,
    ) -> Iterator[Match]:
        """
        Iterate lazily over all non-overlapping matches in the file.

        Parameters
        ----------
        pattern : str
            The regex pattern to search for.
        file_path : str or pathlib.Path
            Path to the file.
        flags : int, optional
            Bitwise OR of :mod:`re` flags. Defaults to ``0``.
        max_span_lines : int or None, optional
            See :meth:`search`.

        Returns
        -------
        Iterator of Match
            Yields :class:`Match` objects lazily. The underlying file is
            closed when the iterator is exhausted or garbage collected.

        Raises
        ------
        ValueError
            If ``max_span_lines`` is not ``>= 1``, if ``pattern`` is
            invalid, or if ``flags`` contains :data:`re.LOCALE`.
        OSError
            If the file cannot be opened.

        Examples
        --------
        >>> from file_re import file_re
        >>> for m in file_re.finditer(r"\\bERROR\\b", "server.log", max_span_lines=1):
        ...     print(m.span(), m.group())
        """
        _validate_span_lines(max_span_lines)
        _check_flags(flags)
        return _MatchIterator(
            _finditer(pattern, _to_str_path(file_path), flags, max_span_lines=max_span_lines)
        )

    @staticmethod
    def compile(pattern: str, flags: int = 0) -> Pattern:
        """
        Compile a regex pattern into a reusable :class:`Pattern` object.

        Parameters
        ----------
        pattern : str
            The regex source string.
        flags : int, optional
            Bitwise OR of :mod:`re` flags. Defaults to ``0``.

        Returns
        -------
        Pattern
            A compiled pattern that exposes ``search``, ``match``,
            ``findall``, and ``finditer`` methods.

        Raises
        ------
        ValueError
            If ``pattern`` is invalid, or if ``flags`` contains
            :data:`re.LOCALE`.
        """
        _check_flags(flags)
        return Pattern(pattern, flags)
