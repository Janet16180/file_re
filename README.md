# file_re

`file_re` is a Python library written in Rust aimed at providing robust and efficient regular expression operations on large files, including compressed files such as `.gz` and `.xz`. The goal of this library is to handle huge files in the order of gigabytes (GB) seamlessly.

## Features

- **Fast and efficient**: Utilizes Rust for performance improvements.
- **Supports Large Files**: Capable of parsing files in gigabytes.
- **Compressed Files**: Supports reading and searching within `.gz` and `.xz` compressed files.
- **Flexible**: Similar interface to Python's built-in `re` module.

## 🚧 Under Development

**Note:** This repository is currently under active development and is not yet available on PyPI. Please refrain from using this library in production environments as interfaces and functionalities are subject to change. The library will be uploaded to PyPI once it is ready for public use.

## Installation

### 1. Create a Virtual Environment

Creating a virtual environment helps you manage dependencies and isolate your project from other Python projects on your machine.

```bash
python -m venv venv
```


### 2. Install Required Dependencies
```bash
pip install -r requirements.txt
```


### 3. Install file_re
```bash
cd file_re
maturin develop --release
```

## To run unit test
```bash
cd unit_tests
python -m pytest -v
```

## Usage
```python
from file_re import file_re
from pathlib import Path

# Define the path to the file
file_path = Path('path/to/your/big_file.txt')

# Search for a specific pattern
match = file_re.search(r"(\d{3})-(\d{3})-(\d{4})", file_path)

# Mimic the behavior of Python's re.search
print("Full match:", match.group(0))
print("Group 1:", match.group(1))
print("Group 2:", match.group(2))
print("Group 3:", match.group(3))

match = file_re.search(r"(?P<username>[\w\.-]+)@(?P<domain>[\w]+)\.\w+", file_path)

# Mimic the behavior of Python's re.search with named groups
print("Full match:", match.group(0))
print("Username:", match.group("username"))
print("Domain:", match.group("domain"))

# Find all matches
matches = file_re.findall(r"(\d{3})-(\d{3})-(\d{4})", file_path)
print(matches)

# You can read direclty from compressed files
file_path = Path('path/to/your/big_file.txt.gz')
matches = file_re.findall(r"(\d{3})-(\d{3})-(\d{4})", file_path)
print(matches)
```