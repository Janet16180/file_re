from ._file_re import (
    search_single_line,
    search_multi_line,
    findall_single_line,
    findall_multi_line
)
from pathlib import Path
from typing import Union

class Match:
    def __init__(self, match_str, start, end, matchs_list, matchs_dict):
        """
        Initializes a Match object.

        Args:
            match_str (str): The full match string.
            start (int): The start position of the match.
            end (int): The end position of the match.
            matchs_list (list): A list of all matched groups.
            matchs_dict (dict): A dictionary of named matched groups.
        """
        self.__match_str = match_str
        self.__start = start
        self.__end = end
        self.__span = (start, end)
        self.__matchs_list = matchs_list
        self.__matchs_dict = matchs_dict


    def span(self):
        """
        Returns the span (start, end) of the match.

        Returns:
            tuple: A tuple containing the start and end positions.
        """
        return self.__span
    
    def start(self):
        """
        Returns the start position of the match.

        Returns:
            int: The start position of the match.
        """
        return self.__start
    
    def end(self):
        """
        Returns the end position of the match.

        Returns:
            int: The end position of the match.
        """
        return self.__end
    
    def group(self, *args):
        """
        Returns one or more subgroups of the match.

        If no arguments are given, it returns the entire match string.
        If a single integer or string is given, it returns the corresponding subgroup.
        If multiple arguments are given, it returns a tuple of the corresponding subgroups.

        Args:
            *args: One or more group indices (integers) or group names (strings).

        Returns:
            Union[str, tuple]: The specified subgroup(s) of the match.
        """
        result_groups = []
        for arg in args:
            if isinstance(arg, int):
                if arg == 0:
                    result_groups.append(self.__match_str)
                else:
                    result_groups.append(self.__matchs_list[arg-1])
            elif isinstance(arg, str):
                result_groups.append(self.__matchs_dict[arg])
    
        if len(result_groups) == 1:
            return result_groups[0]
        
        return tuple(result_groups)
    
    def groups(self):
        """
        Returns a tuple containing all the matched subgroups.

        Returns:
            tuple: A tuple containing all the matched subgroups.
        """
        return tuple(self.__matchs_list)
    
    def groupdict(self):
        """
        Returns a dictionary containing all the named matched subgroups.

        Returns:
            dict: A dictionary containing all the named matched subgroups.
        """
        return self.__matchs_dict
    
    def __str__(self):
        """
        Returns a string representation of the Match object.

        Returns:
            str: A string representation of the Match object.
        """
        return f"<file_re.Match object; span={self.__span}, match='{self.__match_str}'>"
    
    def __repr__(self):
        """
        Returns a string representation of the Match object.

        Returns:
            str: A string representation of the Match object.
        """
        return f"<file_re.Match object; span={self.__span}, match='{self.__match_str}'>"
                

class file_re:

    @staticmethod
    def search(regex, file_path, multiline=False):
        """
        Search the first occurrence of the regex in the file.

        Args:
            regex (str): The regular expression pattern to search for. This should be
                a valid regex pattern supported by the `re` module.
            file_path (Union[str, Path]): The path to the file, provided as either a
                string or a Path object. The file will be read, and the regex applied
                to its content.
            multiline (bool, optional): If True, allows the regex to match across
                multiple lines. Defaults to False.

        Returns:
            Match: A Match object containing information about the match, or None if
            no match is found.
        """
        if isinstance(file_path, Path):
            file_path = str(file_path)

        if multiline:
            result = search_multi_line(regex, file_path)
        else:
            result = search_single_line(regex, file_path)

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
    def findall(regex, file_path, multiline=False):
        """
        Find all occurrences of the regex in the file.

        Args:
            regex (str): The regular expression pattern to search for. The pattern must be 
                a valid regex expression supported by the `re` module.
            file_path (Union[str, Path]): The path to the file, as either a string or
                a Path object. The file will be read and the regex applied to its content.
            multiline (bool, optional): If True, allows the regex to match across
                multiple lines. Defaults to False.

        Returns:
            list: A list of tuples containing all matches found. If there are multiple
            capturing groups, each match is a tuple containing the groups. If there is 
            only one capturing group, the list contains strings representing the matches.
        """
        if isinstance(file_path, Path):
            file_path = str(file_path)
    

        if multiline:
            match_list = findall_multi_line(regex, file_path)
        else:
            match_list = findall_single_line(regex, file_path)

        if match_list:
            if len(match_list[0]) == 1:
                match_list = [item for sublist in match_list for item in sublist]
            else:
                match_list = [tuple(sublist[1:]) for sublist in match_list]
        
        return match_list

__all__ = [file_re]