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
                