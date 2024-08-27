from ._file_re import search_line_by_line


class Match:
    def __init__(self, match_str, start, end, matchs_list, matchs_dict):
        self.__match_str = match_str
        self.__start = start
        self.__end = end
        self.__span = (start, end)
        self.__matchs_list = matchs_list
        self.__matchs_dict = matchs_dict


    def span(self):
        return self.__span
    
    def start(self):
        return self.__start
    
    def end(self):
        return self.__end
    
    def group(self, *args):
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
        return tuple(self.__matchs_list)
    
    def groupdict(self):
        return self.__matchs_dict
    
    def __str__(self):
        return self.__match_str
    
    def __repr__(self):
        return f"<file_re.Match object; span={self.span}, match='{self.__match_str}'>"
                

class file_re:

    @staticmethod
    def search(regex, file_path):
        result = search_line_by_line(regex, file_path)

        match = None
        if result:

            match = Match(
                match_str=result.match_str(),
                start=result.start(),
                end=result.end(),
                matchs_list=result.groups(),
                matchs_dict=result.named_groups()
            )
        return match

__all__ = [file_re]