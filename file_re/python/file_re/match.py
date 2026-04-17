from typing import Dict, List, Optional, Tuple, Union


class Match:
    """
    Represents a single regex match against a file.

    A ``Match`` mirrors the public surface of :class:`re.Match`: it exposes
    ``span()``, ``start()``, ``end()``, ``group()``, ``groups()``, and
    ``groupdict()``. Non-participating capture groups are represented by
    ``None`` (not the empty string), matching :class:`re.Match`.

    Parameters
    ----------
    match_str : str
        The text of the whole match (group 0).
    start : int
        Character offset (inclusive) where the match begins in the file.
    end : int
        Character offset (exclusive) where the match ends in the file.
    matchs_list : list of (str or None)
        Captured subgroups in order. A group that did not participate in
        the match is ``None``.
    matchs_dict : dict of str to (str or None)
        Named captured subgroups. A named group that did not participate
        in the match is ``None``.
    """

    def __init__(
        self,
        match_str: str,
        start: int,
        end: int,
        matchs_list: List[Optional[str]],
        matchs_dict: Dict[str, Optional[str]],
    ) -> None:
        self.__match_str = match_str
        self.__start = start
        self.__end = end
        self.__span = (start, end)
        self.__matchs_list = matchs_list
        self.__matchs_dict = matchs_dict

    def span(self) -> Tuple[int, int]:
        """
        Return the character span of the match.

        Returns
        -------
        tuple of (int, int)
            A ``(start, end)`` pair of character offsets into the file.
        """
        return self.__span

    def start(self) -> int:
        """
        Return the starting character offset of the match.

        Returns
        -------
        int
            Character offset (inclusive) where the match begins.
        """
        return self.__start

    def end(self) -> int:
        """
        Return the ending character offset of the match.

        Returns
        -------
        int
            Character offset (exclusive) where the match ends.
        """
        return self.__end

    def group(
        self, *args: Union[int, str]
    ) -> Union[Optional[str], Tuple[Optional[str], ...]]:
        """
        Return one or more subgroups of the match.

        With no arguments, returns the whole match (group 0). With one
        integer or string, returns the corresponding subgroup. With
        multiple arguments, returns a tuple of the corresponding subgroups.

        Parameters
        ----------
        *args : int or str
            Group indices (integers) or group names (strings). Index ``0``
            refers to the whole match.

        Returns
        -------
        str or None or tuple of (str or None)
            A single group value (``None`` if the group did not
            participate) when exactly one argument is given, otherwise a
            tuple of group values. With no arguments, returns the whole
            match string.

        Raises
        ------
        IndexError
            If an integer index is out of range.
        KeyError
            If a string name does not correspond to a named group.

        Examples
        --------
        >>> m.group()
        'error: disk full'
        >>> m.group(1)
        'disk full'
        >>> m.group('level', 'msg')
        ('error', 'disk full')
        """
        if not args:
            return self.__match_str

        result_groups: List[Optional[str]] = []
        for arg in args:
            if isinstance(arg, int):
                if arg == 0:
                    result_groups.append(self.__match_str)
                else:
                    result_groups.append(self.__matchs_list[arg - 1])
            elif isinstance(arg, str):
                result_groups.append(self.__matchs_dict[arg])

        if len(result_groups) == 1:
            return result_groups[0]

        return tuple(result_groups)

    def groups(self) -> Tuple[Optional[str], ...]:
        """
        Return all captured subgroups as a tuple.

        Returns
        -------
        tuple of (str or None)
            All capturing groups defined by the pattern, in order.
            Non-participating groups are ``None``.
        """
        return tuple(self.__matchs_list)

    def groupdict(self) -> Dict[str, Optional[str]]:
        """
        Return a mapping of named subgroups.

        Returns
        -------
        dict of str to (str or None)
            Named capturing groups defined by the pattern. A group that
            did not participate in the match maps to ``None``.
        """
        return self.__matchs_dict

    def __str__(self) -> str:
        return f"<file_re.Match object; span={self.__span}, match='{self.__match_str}'>"

    def __repr__(self) -> str:
        return f"<file_re.Match object; span={self.__span}, match='{self.__match_str}'>"
