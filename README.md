# file_re

`file_re` is a Python library written in Rust aimed at providing robust and efficient regular expression operations on large files, including compressed files such as `.gz` and `.xz`. The goal of this library is to handle huge files in the order of gigabytes (GB) seamlessly.

## Features

- **Fast and efficient**: Utilizes Rust for performance improvements.
- **Supports Large Files**: Capable of parsing files in gigabytes.
- **Compressed Files**: Supports reading and searching within `.gz` and `.xz` compressed files.
- **Flexible**: Similar interface to Python's built-in `re` module.
- **Memory Efficient**: Multiple modes for handling multi-line patterns without excessive memory usage.

## Usage

### Basic Usage

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
```

### Compressed Files

```python
# You can read directly from compressed files
file_path = Path('path/to/your/big_file.txt.gz')
matches = file_re.findall(r"(\d{3})-(\d{3})-(\d{4})", file_path)
```

### Multi-line Patterns

#### Using `multiline=True` (loads entire file into memory)
```python
# For regex that requires multiple lines - loads entire file
matches = file_re.search(r"<body>[\s\S]+</body>", file_path, multiline=True)
print(matches.group(0))
```

#### Using `num_lines` (memory-efficient sliding window)
```python
# Memory-efficient multi-line matching using sliding window
match = file_re.search(r"hi\nword", file_path, num_lines=2)
print(match.group(0))

# For patterns that can span multiple lines with longest match
# This will find the longest sequence of repeated "hi\n" patterns
match = file_re.search(r"(hi\n)+", file_path, num_lines=3)
print(match.group(0))

# Works with capturing groups and named groups
match = file_re.search(r"(?P<greeting>hi)\n(?P<noun>word)", file_path, num_lines=2)
print("Greeting:", match.group("greeting"))
print("Noun:", match.group("noun"))

# Also works with findall
matches = file_re.findall(r"hi\nworld", file_path, num_lines=2)
print(matches)
```

## Modes of Operation

### 1. Single Line Mode (Default)
- **Memory Usage**: Very low - processes one line at a time
- **Use Case**: Patterns that don't span multiple lines
- **Performance**: Fastest for single-line patterns

```python
match = file_re.search(r"\d+", file_path)  # Default mode
```

### 2. Multi-line Mode (`multiline=True`)
- **Memory Usage**: High - loads entire file into RAM
- **Use Case**: Complex patterns that need the entire file context
- **Performance**: Fast regex operations, but high memory cost

```python
match = file_re.search(r"pattern.*\n.*pattern", file_path, multiline=True)
```

### 3. Sliding Window Mode (`num_lines=N`)
- **Memory Usage**: Low - maintains only N lines in memory
- **Use Case**: Multi-line patterns with limited line span
- **Performance**: Memory efficient with good performance
- **Behavior**: Uses a FIFO buffer of N lines, finds longest possible matches

```python
match = file_re.search(r"pattern\npattern", file_path, num_lines=2)
```

## Algorithm Details for `num_lines`

The `num_lines` feature implements a sliding window algorithm:

1. **Buffer Management**: Maintains a FIFO buffer of exactly `num_lines` lines
2. **Pattern Matching**: Applies regex to the current buffer content on each line read
3. **Longest Match**: When a match is found, continues reading `num_lines` additional lines to find the longest possible match
4. **Memory Efficiency**: Never loads more than `num_lines` into memory at once

### Example Behavior

Given a file:
```
word
word  
word
hi
hi
hi
hi
```

And regex `r"(hi\n?)+"` with `num_lines=3`:

1. When first "hi" is encountered, a match is found
2. Algorithm continues for 2 more lines (num_lines)
3. Returns the longest match: `"hi\nhi\nhi"`

## Limitations

1. **Default Line-by-Line Processing**:
   - **Memory Efficiency**: By default, `file_re` reads files line by line and applies the regular expression to each line individually. This approach is memory efficient as it avoids loading the entire file into RAM.
   - **Pattern Constraints**: This mode may not work effectively for regex patterns that span across multiple lines.

2. **Multiline Mode**:
   - **Full File Loading**: When the multiline mode is enabled, the entire file is loaded into RAM to perform the regex operation. This is necessary for regex patterns that require matching across multiple lines.
   - **Increased RAM Usage**: Loading large files (in gigabytes) into RAM can lead to significant memory consumption. This may not be suitable for systems with limited memory.
   - **Performance Trade-offs**: While enabling multiline mode can result in faster `findall` operations for certain patterns, it comes at the cost of higher memory usage.

3. **Sliding Window Mode (`num_lines`)**:
   - **Pattern Span Limit**: Patterns cannot span more than `num_lines` lines
   - **Match Context**: Only finds matches within the sliding window context
   - **Overlapping Patterns**: May find overlapping matches due to the sliding nature

4. **Limited Flag Support**:
   - **Flag Limitations**: Currently, flags such as `re.IGNORECASE` or `re.MULTILINE` are not supported as function parameters (though inline flags like `(?i)` work)
   - **Future Enhancements**: Support for these flags is planned for future releases, which will enhance the flexibility and usability of the library.

5. **Parameter Conflicts**:
   - **Exclusive Options**: Cannot use `multiline=True` and `num_lines` together
   - **Validation**: `num_lines` must be greater than 0

## Performance Recommendations

- **Small patterns within single lines**: Use default mode
- **Large files with multi-line patterns (≤ N lines)**: Use `num_lines=N`
- **Complex patterns requiring full file context**: Use `multiline=True` (if you have sufficient RAM)
- **Compressed files**: All modes support `.gz` and `.xz` files transparently

Users are encouraged to assess their specific needs and system capabilities when using `file_re`, especially when working with extremely large files or complex multiline regex patterns.