from .core import file_re_cls
from .match import Match
from .pattern import Pattern

__version__ = "2.0.0"

file_re = file_re_cls
search = file_re_cls.search
match = file_re_cls.match
findall = file_re_cls.findall
finditer = file_re_cls.finditer
compile = file_re_cls.compile

__all__ = [
    "search",
    "match",
    "findall",
    "finditer",
    "compile",
    "Match",
    "Pattern",
    "file_re",
    "__version__",
]
