use pyo3::exceptions::{PyOSError, PyValueError};
use pyo3::prelude::*;
use regex::{Captures, Regex, RegexBuilder};
use std::collections::{HashMap, VecDeque};
use std::io::BufRead;
use std::sync::Arc;

mod read_file;

const RE_IGNORECASE: u32 = 2;
const RE_LOCALE: u32 = 4;
const RE_MULTILINE: u32 = 8;
const RE_DOTALL: u32 = 16;
const RE_VERBOSE: u32 = 64;
const RE_ASCII: u32 = 256;

fn build_regex(pattern: &str, flags: u32) -> PyResult<Regex> {
    if flags & RE_LOCALE != 0 {
        return Err(PyValueError::new_err(
            "re.LOCALE is not supported by file_re (no equivalent in Rust regex engine)",
        ));
    }
    let mut builder = RegexBuilder::new(pattern);
    builder.case_insensitive(flags & RE_IGNORECASE != 0);
    builder.multi_line(flags & RE_MULTILINE != 0);
    builder.dot_matches_new_line(flags & RE_DOTALL != 0);
    builder.ignore_whitespace(flags & RE_VERBOSE != 0);
    if flags & RE_ASCII != 0 {
        builder.unicode(false);
    }
    builder
        .build()
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

fn io_to_py(e: std::io::Error) -> PyErr {
    PyOSError::new_err(e.to_string())
}

fn invalid_span_lines() -> PyErr {
    PyValueError::new_err("max_span_lines must be >= 1")
}

#[pyclass]
struct Match {
    #[pyo3(get)]
    groups: Vec<Option<String>>,
    #[pyo3(get)]
    named_groups: HashMap<String, Option<String>>,
    #[pyo3(get)]
    start: usize,
    #[pyo3(get)]
    end: usize,
    #[pyo3(get)]
    match_str: String,
}

fn build_match(re: &Regex, caps: &Captures<'_>, haystack: &str, abs_char_base: usize) -> Match {
    let whole = caps.get(0).unwrap();
    let start_byte = whole.start();
    let end_byte = whole.end();
    let start_char = haystack[..start_byte].chars().count();
    let end_char = haystack[..end_byte].chars().count();
    let match_str = whole.as_str().to_string();

    let groups: Vec<Option<String>> = (1..caps.len())
        .map(|i| caps.get(i).map(|m| m.as_str().to_string()))
        .collect();

    let mut named_groups: HashMap<String, Option<String>> = HashMap::new();
    for name in re.capture_names().flatten() {
        named_groups.insert(
            name.to_string(),
            caps.name(name).map(|m| m.as_str().to_string()),
        );
    }

    Match {
        groups,
        named_groups,
        start: abs_char_base + start_char,
        end: abs_char_base + end_char,
        match_str,
    }
}

fn strip_line_end(line: &mut String) -> bool {
    let had_newline = line.ends_with('\n');
    if had_newline {
        line.pop();
        if line.ends_with('\r') {
            line.pop();
        }
    }
    had_newline
}

fn step_one_char(s: &str, pos: usize) -> usize {
    if pos >= s.len() {
        return s.len() + 1;
    }
    let mut p = pos + 1;
    while p < s.len() && !s.is_char_boundary(p) {
        p += 1;
    }
    p
}

struct LineMeta {
    byte_len: usize,
    char_len: usize,
}

struct LineBuffer {
    lines: VecDeque<LineMeta>,
    text: String,
    abs_char_base: usize,
}

impl LineBuffer {
    fn new() -> Self {
        Self {
            lines: VecDeque::new(),
            text: String::new(),
            abs_char_base: 0,
        }
    }

    fn push(&mut self, line: &str) {
        if !self.lines.is_empty() {
            self.text.push('\n');
        }
        self.text.push_str(line);
        self.lines.push_back(LineMeta {
            byte_len: line.len(),
            char_len: line.chars().count(),
        });
    }

    fn len(&self) -> usize {
        self.lines.len()
    }

    fn evict_front(&mut self) {
        let meta = self.lines.pop_front().unwrap();
        let (drain_bytes, drain_chars) = if self.lines.is_empty() {
            (meta.byte_len, meta.char_len)
        } else {
            (meta.byte_len + 1, meta.char_len + 1)
        };
        self.text.drain(..drain_bytes);
        self.abs_char_base += drain_chars;
    }
}

fn search_full(re: &Regex, text: &str) -> Option<Match> {
    re.captures(text).map(|caps| build_match(re, &caps, text, 0))
}

fn search_single_line(
    re: &Regex,
    mut reader: Box<dyn BufRead + Send>,
) -> PyResult<Option<Match>> {
    let mut line = String::new();
    let mut abs_char = 0usize;
    loop {
        line.clear();
        let bytes = reader.read_line(&mut line).map_err(io_to_py)?;
        if bytes == 0 {
            break;
        }
        let had_nl = strip_line_end(&mut line);
        if let Some(caps) = re.captures(&line) {
            return Ok(Some(build_match(re, &caps, &line, abs_char)));
        }
        abs_char += line.chars().count();
        if had_nl {
            abs_char += 1;
        }
    }
    Ok(None)
}

fn search_window(
    re: &Regex,
    mut reader: Box<dyn BufRead + Send>,
    n: usize,
) -> PyResult<Option<Match>> {
    let mut buf = LineBuffer::new();
    let mut line = String::new();
    loop {
        line.clear();
        let bytes = reader.read_line(&mut line).map_err(io_to_py)?;
        if bytes == 0 {
            break;
        }
        strip_line_end(&mut line);
        buf.push(&line);
        while buf.len() > n {
            buf.evict_front();
        }
        if let Some(caps) = re.captures(&buf.text) {
            return Ok(Some(build_match(re, &caps, &buf.text, buf.abs_char_base)));
        }
    }
    Ok(None)
}

fn match_full(re: &Regex, text: &str) -> Option<Match> {
    re.captures(text).and_then(|caps| {
        if caps.get(0).unwrap().start() == 0 {
            Some(build_match(re, &caps, text, 0))
        } else {
            None
        }
    })
}

fn match_single_line(
    re: &Regex,
    mut reader: Box<dyn BufRead + Send>,
) -> PyResult<Option<Match>> {
    let mut line = String::new();
    let bytes = reader.read_line(&mut line).map_err(io_to_py)?;
    if bytes == 0 {
        return Ok(None);
    }
    strip_line_end(&mut line);
    if let Some(caps) = re.captures(&line) {
        if caps.get(0).unwrap().start() == 0 {
            return Ok(Some(build_match(re, &caps, &line, 0)));
        }
    }
    Ok(None)
}

fn match_window(
    re: &Regex,
    mut reader: Box<dyn BufRead + Send>,
    n: usize,
) -> PyResult<Option<Match>> {
    let mut buf = LineBuffer::new();
    let mut line = String::new();
    while buf.len() < n {
        line.clear();
        let bytes = reader.read_line(&mut line).map_err(io_to_py)?;
        if bytes == 0 {
            break;
        }
        strip_line_end(&mut line);
        buf.push(&line);
        if let Some(caps) = re.captures(&buf.text) {
            if caps.get(0).unwrap().start() == 0 {
                return Ok(Some(build_match(re, &caps, &buf.text, 0)));
            }
        }
    }
    Ok(None)
}

fn caps_to_row(caps: &Captures<'_>) -> Vec<Option<String>> {
    caps.iter()
        .map(|g| g.map(|m| m.as_str().to_string()))
        .collect()
}

fn findall_full(re: &Regex, text: &str) -> Vec<Vec<Option<String>>> {
    re.captures_iter(text).map(|c| caps_to_row(&c)).collect()
}

fn findall_single_line(
    re: &Regex,
    mut reader: Box<dyn BufRead + Send>,
) -> PyResult<Vec<Vec<Option<String>>>> {
    let mut line = String::new();
    let mut out = Vec::new();
    loop {
        line.clear();
        let bytes = reader.read_line(&mut line).map_err(io_to_py)?;
        if bytes == 0 {
            break;
        }
        strip_line_end(&mut line);
        for caps in re.captures_iter(&line) {
            out.push(caps_to_row(&caps));
        }
    }
    Ok(out)
}

fn findall_window(
    re: &Regex,
    mut reader: Box<dyn BufRead + Send>,
    n: usize,
) -> PyResult<Vec<Vec<Option<String>>>> {
    let mut buf = LineBuffer::new();
    let mut line = String::new();
    let mut out: Vec<Vec<Option<String>>> = Vec::new();
    let mut last_match_end: usize = 0;
    loop {
        line.clear();
        let bytes = reader.read_line(&mut line).map_err(io_to_py)?;
        if bytes == 0 {
            break;
        }
        strip_line_end(&mut line);
        buf.push(&line);
        while buf.len() > n {
            buf.evict_front();
        }
        for caps in re.captures_iter(&buf.text) {
            let mat = caps.get(0).unwrap();
            let start_char = buf.text[..mat.start()].chars().count();
            let end_char = buf.text[..mat.end()].chars().count();
            let abs_start = buf.abs_char_base + start_char;
            let abs_end = buf.abs_char_base + end_char;
            if abs_start < last_match_end {
                continue;
            }
            out.push(caps_to_row(&caps));
            last_match_end = abs_end;
        }
    }
    Ok(out)
}

enum IterEngine {
    Full {
        text: Arc<String>,
        byte_cursor: usize,
    },
    SingleLine {
        reader: Box<dyn BufRead + Send>,
        current_line: String,
        line_byte_cursor: usize,
        line_abs_char: usize,
        next_line_abs_char: usize,
        has_line: bool,
        eof: bool,
    },
    Window {
        reader: Box<dyn BufRead + Send>,
        buf: LineBuffer,
        n: usize,
        pending: VecDeque<Match>,
        last_match_end: usize,
        eof: bool,
    },
}

fn advance_iter(re: &Regex, engine: &mut IterEngine) -> PyResult<Option<Match>> {
    match engine {
        IterEngine::Full { text, byte_cursor } => {
            if *byte_cursor > text.len() {
                return Ok(None);
            }
            match re.captures_at(text, *byte_cursor) {
                Some(caps) => {
                    let mat = caps.get(0).unwrap();
                    let m = build_match(re, &caps, text, 0);
                    *byte_cursor = if mat.end() > mat.start() {
                        mat.end()
                    } else {
                        step_one_char(text, mat.end())
                    };
                    Ok(Some(m))
                }
                None => Ok(None),
            }
        }
        IterEngine::SingleLine {
            reader,
            current_line,
            line_byte_cursor,
            line_abs_char,
            next_line_abs_char,
            has_line,
            eof,
        } => loop {
            if !*has_line {
                if *eof {
                    return Ok(None);
                }
                current_line.clear();
                let bytes = reader.read_line(current_line).map_err(io_to_py)?;
                if bytes == 0 {
                    *eof = true;
                    return Ok(None);
                }
                let had_nl = strip_line_end(current_line);
                *line_abs_char = *next_line_abs_char;
                *next_line_abs_char = *line_abs_char
                    + current_line.chars().count()
                    + if had_nl { 1 } else { 0 };
                *line_byte_cursor = 0;
                *has_line = true;
            }
            if *line_byte_cursor > current_line.len() {
                *has_line = false;
                continue;
            }
            match re.captures_at(current_line, *line_byte_cursor) {
                Some(caps) => {
                    let mat = caps.get(0).unwrap();
                    let m = build_match(re, &caps, current_line, *line_abs_char);
                    *line_byte_cursor = if mat.end() > mat.start() {
                        mat.end()
                    } else {
                        step_one_char(current_line, mat.end())
                    };
                    return Ok(Some(m));
                }
                None => {
                    *has_line = false;
                }
            }
        },
        IterEngine::Window {
            reader,
            buf,
            n,
            pending,
            last_match_end,
            eof,
        } => loop {
            if let Some(m) = pending.pop_front() {
                return Ok(Some(m));
            }
            if *eof {
                return Ok(None);
            }
            let mut line = String::new();
            let bytes = reader.read_line(&mut line).map_err(io_to_py)?;
            if bytes == 0 {
                *eof = true;
                continue;
            }
            strip_line_end(&mut line);
            buf.push(&line);
            while buf.len() > *n {
                buf.evict_front();
            }
            for caps in re.captures_iter(&buf.text) {
                let mat = caps.get(0).unwrap();
                let start_char = buf.text[..mat.start()].chars().count();
                let end_char = buf.text[..mat.end()].chars().count();
                let abs_start = buf.abs_char_base + start_char;
                let abs_end = buf.abs_char_base + end_char;
                if abs_start < *last_match_end {
                    continue;
                }
                pending.push_back(build_match(re, &caps, &buf.text, buf.abs_char_base));
                *last_match_end = abs_end;
            }
        },
    }
}

#[pyclass(unsendable)]
struct MatchIter {
    regex: Arc<Regex>,
    engine: IterEngine,
}

#[pymethods]
impl MatchIter {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self, py: Python<'_>) -> PyResult<Option<Match>> {
        let regex = self.regex.clone();
        let engine = &mut self.engine;
        py.detach(|| advance_iter(&regex, engine))
    }
}

fn build_finditer(
    py: Python<'_>,
    regex: Arc<Regex>,
    file_path: &str,
    max_span_lines: Option<usize>,
) -> PyResult<Py<MatchIter>> {
    let engine = match max_span_lines {
        None => {
            let text = py
                .detach(|| read_file::open_file_full_content(file_path))
                .map_err(io_to_py)?;
            IterEngine::Full {
                text: Arc::new(text),
                byte_cursor: 0,
            }
        }
        Some(0) => return Err(invalid_span_lines()),
        Some(1) => {
            let reader = read_file::open_file_as_reader(file_path).map_err(io_to_py)?;
            IterEngine::SingleLine {
                reader,
                current_line: String::new(),
                line_byte_cursor: 0,
                line_abs_char: 0,
                next_line_abs_char: 0,
                has_line: false,
                eof: false,
            }
        }
        Some(n) => {
            let reader = read_file::open_file_as_reader(file_path).map_err(io_to_py)?;
            IterEngine::Window {
                reader,
                buf: LineBuffer::new(),
                n,
                pending: VecDeque::new(),
                last_match_end: 0,
                eof: false,
            }
        }
    };
    Py::new(py, MatchIter { regex, engine })
}

fn search_dispatch(
    py: Python<'_>,
    re: &Regex,
    file_path: &str,
    max_span_lines: Option<usize>,
) -> PyResult<Option<Match>> {
    match max_span_lines {
        None => py.detach(|| {
            let text = read_file::open_file_full_content(file_path).map_err(io_to_py)?;
            Ok(search_full(re, &text))
        }),
        Some(0) => Err(invalid_span_lines()),
        Some(1) => py.detach(|| {
            let reader = read_file::open_file_as_reader(file_path).map_err(io_to_py)?;
            search_single_line(re, reader)
        }),
        Some(n) => py.detach(|| {
            let reader = read_file::open_file_as_reader(file_path).map_err(io_to_py)?;
            search_window(re, reader, n)
        }),
    }
}

fn match_dispatch(
    py: Python<'_>,
    re: &Regex,
    file_path: &str,
    max_span_lines: Option<usize>,
) -> PyResult<Option<Match>> {
    match max_span_lines {
        None => py.detach(|| {
            let text = read_file::open_file_full_content(file_path).map_err(io_to_py)?;
            Ok(match_full(re, &text))
        }),
        Some(0) => Err(invalid_span_lines()),
        Some(1) => py.detach(|| {
            let reader = read_file::open_file_as_reader(file_path).map_err(io_to_py)?;
            match_single_line(re, reader)
        }),
        Some(n) => py.detach(|| {
            let reader = read_file::open_file_as_reader(file_path).map_err(io_to_py)?;
            match_window(re, reader, n)
        }),
    }
}

fn findall_dispatch(
    py: Python<'_>,
    re: &Regex,
    file_path: &str,
    max_span_lines: Option<usize>,
) -> PyResult<Vec<Vec<Option<String>>>> {
    match max_span_lines {
        None => py.detach(|| {
            let text = read_file::open_file_full_content(file_path).map_err(io_to_py)?;
            Ok(findall_full(re, &text))
        }),
        Some(0) => Err(invalid_span_lines()),
        Some(1) => py.detach(|| {
            let reader = read_file::open_file_as_reader(file_path).map_err(io_to_py)?;
            findall_single_line(re, reader)
        }),
        Some(n) => py.detach(|| {
            let reader = read_file::open_file_as_reader(file_path).map_err(io_to_py)?;
            findall_window(re, reader, n)
        }),
    }
}

#[pyfunction]
#[pyo3(signature = (regex, file_path, flags=0, *, max_span_lines=None))]
fn _search(
    py: Python<'_>,
    regex: &str,
    file_path: &str,
    flags: u32,
    max_span_lines: Option<usize>,
) -> PyResult<Option<Match>> {
    let re = build_regex(regex, flags)?;
    search_dispatch(py, &re, file_path, max_span_lines)
}

#[pyfunction]
#[pyo3(signature = (regex, file_path, flags=0, *, max_span_lines=None))]
fn _match(
    py: Python<'_>,
    regex: &str,
    file_path: &str,
    flags: u32,
    max_span_lines: Option<usize>,
) -> PyResult<Option<Match>> {
    let re = build_regex(regex, flags)?;
    match_dispatch(py, &re, file_path, max_span_lines)
}

#[pyfunction]
#[pyo3(signature = (regex, file_path, flags=0, *, max_span_lines=None))]
fn _findall(
    py: Python<'_>,
    regex: &str,
    file_path: &str,
    flags: u32,
    max_span_lines: Option<usize>,
) -> PyResult<Vec<Vec<Option<String>>>> {
    let re = build_regex(regex, flags)?;
    findall_dispatch(py, &re, file_path, max_span_lines)
}

#[pyfunction]
#[pyo3(signature = (regex, file_path, flags=0, *, max_span_lines=None))]
fn _finditer(
    py: Python<'_>,
    regex: &str,
    file_path: &str,
    flags: u32,
    max_span_lines: Option<usize>,
) -> PyResult<Py<MatchIter>> {
    let re = Arc::new(build_regex(regex, flags)?);
    build_finditer(py, re, file_path, max_span_lines)
}

#[pyclass]
struct Pattern {
    regex: Arc<Regex>,
    #[pyo3(get)]
    pattern: String,
    #[pyo3(get)]
    flags: u32,
}

#[pymethods]
impl Pattern {
    #[new]
    #[pyo3(signature = (pattern, flags=0))]
    fn new(pattern: &str, flags: u32) -> PyResult<Self> {
        let regex = Arc::new(build_regex(pattern, flags)?);
        Ok(Self {
            regex,
            pattern: pattern.to_string(),
            flags,
        })
    }

    #[pyo3(signature = (file_path, max_span_lines=None))]
    fn search(
        &self,
        py: Python<'_>,
        file_path: &str,
        max_span_lines: Option<usize>,
    ) -> PyResult<Option<Match>> {
        search_dispatch(py, &self.regex, file_path, max_span_lines)
    }

    #[pyo3(name = "match", signature = (file_path, max_span_lines=None))]
    fn match_(
        &self,
        py: Python<'_>,
        file_path: &str,
        max_span_lines: Option<usize>,
    ) -> PyResult<Option<Match>> {
        match_dispatch(py, &self.regex, file_path, max_span_lines)
    }

    #[pyo3(signature = (file_path, max_span_lines=None))]
    fn findall(
        &self,
        py: Python<'_>,
        file_path: &str,
        max_span_lines: Option<usize>,
    ) -> PyResult<Vec<Vec<Option<String>>>> {
        findall_dispatch(py, &self.regex, file_path, max_span_lines)
    }

    #[pyo3(signature = (file_path, max_span_lines=None))]
    fn finditer(
        &self,
        py: Python<'_>,
        file_path: &str,
        max_span_lines: Option<usize>,
    ) -> PyResult<Py<MatchIter>> {
        build_finditer(py, self.regex.clone(), file_path, max_span_lines)
    }

    fn __repr__(&self) -> String {
        format!("Pattern(pattern={:?}, flags={})", self.pattern, self.flags)
    }
}

#[pymodule]
#[pyo3(name = "_file_re")]
fn file_re(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(_search, m)?)?;
    m.add_function(wrap_pyfunction!(_match, m)?)?;
    m.add_function(wrap_pyfunction!(_findall, m)?)?;
    m.add_function(wrap_pyfunction!(_finditer, m)?)?;
    m.add_class::<Match>()?;
    m.add_class::<Pattern>()?;
    m.add_class::<MatchIter>()?;
    Ok(())
}
