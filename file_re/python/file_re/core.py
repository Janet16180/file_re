from pathlib import Path
from typing import Union, List, Optional
from ._file_re import (
    _search_single_line,
    _search_multi_line,
    _search_num_lines,
    _findall_single_line,
    _findall_multi_line,
    _findall_num_lines,
)
from .match import Match


class file_re_cls:

    @staticmethod
    def search(
        regex: str, 
        file_path: Union[str, Path], 
        multiline: bool = False,
        num_lines: Optional[int] = None
    ) -> Match:
        """
        Search the first occurrence of the regex in the file.

        Args:
            regex (str): The regular expression pattern to search for. This should be
                a valid regex pattern supported by the `re` module.
            file_path (Union[str, Path]): The path to the file, provided as either a
                string or a Path object. The file will be read, and the regex applied
                to its content.
            multiline (bool, optional): If True, allows the regex to match across
                multiple lines by loading the entire file into memory. Defaults to False.
            num_lines (int, optional): If provided, uses a sliding window approach
                with the specified number of lines to match patterns across multiple
                lines without loading the entire file into memory. Cannot be used
                together with multiline=True.

        Returns:
            Match: A Match object containing information about the match, or None if
            no match is found.

        Raises:
            ValueError: If both multiline=True and num_lines are specified, or if
                num_lines is less than or equal to 0.
        """
        if isinstance(file_path, Path):
            file_path = str(file_path)

        # Validate parameters
        if multiline and num_lines is not None:
            raise ValueError("Cannot use both multiline=True and num_lines. Choose one approach.")
        
        if num_lines is not None and num_lines <= 0:
            raise ValueError("num_lines must be greater than 0")

        # Choose the appropriate search method
        if num_lines is not None:
            result = _search_num_lines(regex, file_path, num_lines)
        elif multiline:
            result = _search_multi_line(regex, file_path)
        else:
            result = _search_single_line(regex, file_path)

        match = None
        if result:
            match = Match(
                match_str=result.match_str,
                start=result.start,
                end=result.end,
                matchs_list=result.groups,
                matchs_dict=result.named_groups,
            )

        return match

    @staticmethod
    def findall(
        regex: str, 
        file_path: Union[str, Path], 
        multiline: bool = False,
        num_lines: Optional[int] = None
    ) -> List:
        """
        Find all occurrences of the regex in the file.

        Args:
            regex (str): The regular expression pattern to search for. The pattern must be
                a valid regex expression supported by the `re` module.
            file_path (Union[str, Path]): The path to the file, as either a string or
                a Path object. The file will be read and the regex applied to its content.
            multiline (bool, optional): If True, allows the regex to match across
                multiple lines by loading the entire file into memory. Defaults to False.
            num_lines (int, optional): If provided, uses a sliding window approach
                with the specified number of lines to match patterns across multiple
                lines without loading the entire file into memory. Cannot be used
                together with multiline=True.

        Returns:
            list: A list of tuples containing all matches found. If there are multiple
            capturing groups, each match is a tuple containing the groups. If there is
            only one capturing group, the list contains strings representing the matches.

        Raises:
            ValueError: If both multiline=True and num_lines are specified, or if
                num_lines is less than or equal to 0.
        """
        if isinstance(file_path, Path):
            file_path = str(file_path)

        # Validate parameters
        if multiline and num_lines is not None:
            raise ValueError("Cannot use both multiline=True and num_lines. Choose one approach.")
        
        if num_lines is not None and num_lines <= 0:
            raise ValueError("num_lines must be greater than 0")

        # Choose the appropriate findall method
        if num_lines is not None:
            match_list = _findall_num_lines(regex, file_path, num_lines)
        elif multiline:
            match_list = _findall_multi_line(regex, file_path)
        else:
            match_list = _findall_single_line(regex, file_path)

        if match_list:
            if len(match_list[0]) == 1:
                match_list = [item for sublist in match_list for item in sublist]
            else:
                match_list = [tuple(sublist[1:]) for sublist in match_list]

        return match_list