from .core import file_re_cls
from .match import Match


file_re_instance = file_re_cls()
search = file_re_instance.search
findall = file_re_instance.findall


__all__ = ['search', 'findall', 'Match']
