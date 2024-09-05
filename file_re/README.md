# file_re

`file_re` is a Python library written in Rust aimed at providing robust and efficient regular expression operations on large files, including compressed files such as `.gz` and `.xz`. The goal of this library is to handle huge files in the order of gigabytes (GB) seamlessly.

## Features

- **Fast and efficient**: Utilizes Rust for performance improvements.
- **Supports Large Files**: Capable of parsing files in gigabytes.
- **Compressed Files**: Supports reading and searching within `.gz` and `.xz` compressed files.
- **Flexible**: Similar interface to Python's built-in `re` module.


## Usage

```python
import file_re
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

# For regex that requires multiple lines you have to enable the multiline mode
matches = file_re.search(r"<body>[\s\S]+</body>", file_path, multiline=True)
print(matches.group(0))
```

## Limitations

1. **Default Line-by-Line Processing**:
   - **Memory Efficiency**: By default, `file_re` reads files line by line and applies the regular expression to each line individually. This approach is memory efficient as it avoids loading the entire file into RAM.
   - **Pattern Constraints**: This mode may not work effectively for regex patterns that span across multiple lines. 

2. **Multiline Mode**:
   - **Full File Loading**: When the multiline mode is enabled, the entire file is loaded into RAM to perform the regex operation. This is necessary for regex patterns that require matching across multiple lines.
   - **Increased RAM Usage**: Loading large files (in gigabytes) into RAM can lead to significant memory consumption. This may not be suitable for systems with limited memory.
   - **Performance Trade-offs**: While enabling multiline mode can result in faster `findall` operations for certain patterns, it comes at the cost of higher memory usage.

3. **Limited Flag Support**:
   - **Flag Limitations**: Currently, flags such as `re.IGNORECASE` or `re.MULTILINE` are not supported.
   - **Future Enhancements**: Support for these flags is planned for future releases, which will enhance the flexibility and usability of the library.


Users are encouraged to assess their specific needs and system capabilities when using `file_re`, especially when working with extremely large files or complex multiline regex patterns.