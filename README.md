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