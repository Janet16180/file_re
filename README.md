# file_re

`file_re` is a Python library written in Rust aimed at providing robust and efficient regular expression operations on large files, including compressed files such as `.gz` and `.xz`. The goal of this library is to handle huge files in the order of gigabytes (GB) seamlessly.

## Features

- **Fast and efficient**: Utilizes Rust for performance improvements.
- **Supports Large Files**: Capable of parsing files in gigabytes.
- **Compressed Files**: Supports reading and searching within `.gz` and `.xz` compressed files.
- **Flexible**: Similar interface to Python's built-in `re` module.
- **Limited Multiline Support**: Efficiently search patterns spanning a limited number of lines using the `num_lines` parameter.


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

# For regex that requires multiple lines you have to enable the multiline mode
matches = file_re.search(r"<body>[\s\S]+</body>", file_path, multiline=True)
print(matches.group(0))

# Search patterns spanning a limited number of lines (memory efficient)
# This finds the last match that spans at most 3 lines
log_match = file_re.search(r"ERROR.*\n.*\n.*FAILED", file_path, num_lines=3)
if log_match:
    print("Error found:", log_match.group(0))

# Find configuration blocks that span multiple lines
config_match = file_re.search(r"^\[database\].*\nhost.*\nport.*", file_path, num_lines=5)
if config_match:
    print("Database config:", config_match.group(0))
```

## The `num_lines` Parameter

The `num_lines` parameter provides a memory-efficient way to search for patterns that span multiple lines without loading the entire file into memory. This feature is particularly useful for large files where full multiline mode would be too memory-intensive.

### How it works

- **FIFO Queue Approach**: Uses a sliding window (FIFO queue) that maintains at most `num_lines` lines in memory
- **Continuous Matching**: As each new line is read, the regex is applied to the current window
- **Last Match Priority**: Returns the last match found, ensuring you get the most recent or complete pattern
- **Memory Efficient**: Only keeps the specified number of lines in memory, regardless of file size

### When to use `num_lines`

1. **Log File Analysis**: Finding error patterns that span multiple lines in large log files
   ```python
   # Find stack traces that span up to 10 lines
   error = file_re.search(r"Exception.*(\n.*){1,9}", "app.log", num_lines=10)
   ```

2. **Configuration File Parsing**: Extracting configuration blocks
   ```python
   # Find database configuration sections
   db_config = file_re.search(r"\[database\].*\nhost.*\nport.*", "config.ini", num_lines=5)
   ```

3. **Data Records**: Processing multi-line records in structured files
   ```python
   # Find customer records spanning multiple lines
   customer = file_re.search(r"CUSTOMER_ID.*\n.*ADDRESS.*\n.*PHONE.*", "data.txt", num_lines=4)
   ```

4. **Code Analysis**: Finding functions or classes in source code
   ```python
   # Find function definitions with their first few lines
   function = file_re.search(r"def process_data.*\n.*\n.*", "code.py", num_lines=5)
   ```

### Example: Processing Large Log Files

```python
from file_re import file_re

# Large log file (multiple GB)
log_file = "application.log"

# Find the last occurrence of a multi-line error pattern
# This is memory efficient even for huge files
error_pattern = r"ERROR.*database.*\n.*connection.*\n.*timeout"
last_error = file_re.search(error_pattern, log_file, num_lines=3)

if last_error:
    print(f"Last database error found at position {last_error.start()}:")
    print(last_error.group(0))

# Find all multi-line warning patterns
warning_pattern = r"WARN.*\n.*retry.*\n.*failed"
all_warnings = file_re.findall(warning_pattern, log_file, num_lines=3)
print(f"Found {len(all_warnings)} warning sequences")
```

### Performance Comparison

| Mode | Memory Usage | Speed | Use Case |
|------|-------------|-------|----------|
| **Single-line** | Very Low | Fast | Patterns within single lines |
| **`num_lines=N`** | Low (N lines) | Fast | Limited multi-line patterns |
| **`multiline=True`** | High (entire file) | Variable | Complex multi-line patterns |

## Limitations

1. **Default Line-by-Line Processing**:
   - **Memory Efficiency**: By default, `file_re` reads files line by line and applies the regular expression to each line individually. This approach is memory efficient as it avoids loading the entire file into RAM.
   - **Pattern Constraints**: This mode may not work effectively for regex patterns that span across multiple lines.

2. **Limited Multiline Support (`num_lines`)**: 
   - **Fixed Window Size**: The `num_lines` parameter provides a fixed sliding window, which may not capture patterns that span more lines than specified.
   - **Last Match Only**: For `search()`, only the last match found is returned, not the first occurrence.
   - **Pattern Complexity**: Very complex patterns spanning many lines may still require full multiline mode.

3. **Full Multiline Mode**:
   - **Full File Loading**: When the multiline mode is enabled, the entire file is loaded into RAM to perform the regex operation. This is necessary for regex patterns that require matching across multiple lines.
   - **Increased RAM Usage**: Loading large files (in gigabytes) into RAM can lead to significant memory consumption. This may not be suitable for systems with limited memory.
   - **Performance Trade-offs**: While enabling multiline mode can result in faster `findall` operations for certain patterns, it comes at the cost of higher memory usage.

4. **Limited Flag Support**:
   - **Flag Limitations**: Currently, flags such as `re.IGNORECASE` or `re.MULTILINE` are not supported.
   - **Future Enhancements**: Support for these flags is planned for future releases, which will enhance the flexibility and usability of the library.


Users are encouraged to assess their specific needs and system capabilities when using `file_re`, especially when working with extremely large files or complex multiline regex patterns.