import os
import gzip
import lzma
from pathlib import Path


def read_file(path):
    if isinstance(path, str):
        path = Path(path)

    extension = path.suffix
    if extension == '.gz':
        with gzip.open(path, 'r') as f:
            return f.read()
    elif extension == '.xz':
        with lzma.open(path, 'r') as f:
            return f.read()
    elif extension == '.txt':
        with open(path, 'r') as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file extension: {extension}")
