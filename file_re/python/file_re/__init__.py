from .core import file_re_cls
from .match import Match


search = file_re_cls.search
findall = file_re_cls.findall


__all__ = ["search", "findall", "Match"]
