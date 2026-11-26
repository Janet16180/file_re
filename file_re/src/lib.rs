use pyo3::exceptions::{PyOSError, PyValueError};
use pyo3::prelude::*;
use regex_automata::meta::{self, Regex};
use regex_automata::util::captures::Captures;
use regex_automata::util::syntax;
use regex_automata::PatternID;
use std::collections::HashMap;
use std::error::Error;
use std::sync::atomic::Ordering;
use std::sync::Arc;

mod read_file;
mod scanner;

use scanner::Scanner;

const RE_IGNORECASE: u32 = 2;
const RE_LOCALE: u32 = 4;
const RE_MULTILINE: u32 = 8;
const RE_DOTALL: u32 = 16;
const RE_VERBOSE: u32 = 64;
const RE_ASCII: u32 = 256;

/// A compiled regex plus the metadata needed to build `Match` objects.
struct Compiled {
    re: Regex,
    /// `(name, group index)` for every named group.
    names: Vec<(String, usize)>,
}

fn build_regex(pattern: &str, flags: u32) -> PyResult<Compiled> {
    if flags & RE_LOCALE != 0 {
        return Err(PyValueError::new_err(
            "re.LOCALE is not supported by file_re (no equivalent in Rust regex engine)",
        ));
    }
    let syntax = syntax::Config::new()
        .case_insensitive(flags & RE_IGNORECASE != 0)
        .multi_line(flags & RE_MULTILINE != 0)
        .dot_matches_new_line(flags & RE_DOTALL != 0)
        .ignore_whitespace(flags & RE_VERBOSE != 0)
        .unicode(flags & RE_ASCII == 0);
    // Same limits the `regex` crate applies by default.
    let config = meta::Config::new()
        .utf8_empty(true)
        .nfa_size_limit(Some(10 * (1 << 20)))
        .hybrid_cache_capacity(2 * (1 << 20));
    let re = Regex::builder()
        .syntax(syntax)
        .configure(config)
        .build(pattern)
        .map_err(|e| {
            // The useful message (with the caret diagram) is the innermost cause.
            let mut cause: &dyn Error = &e;
            while let Some(next) = cause.source() {
                cause = next;
            }
            PyValueError::new_err(cause.to_string())
        })?;
    let names = re
        .group_info()
        .pattern_names(PatternID::ZERO)
        .enumerate()
        .filter_map(|(i, name)| name.map(|n| (n.to_string(), i)))
        .collect();
    Ok(Compiled { re, names })
}

fn io_to_py(e: std::io::Error) -> PyErr {
    PyOSError::new_err(e.to_string())
}

fn open_scanner(file_path: &str, max_span_lines: Option<usize>) -> PyResult<Scanner> {
    if max_span_lines == Some(0) {
        return Err(PyValueError::new_err("max_span_lines must be >= 1"));
    }
    let (reader, size_hint) = read_file::open(file_path).map_err(io_to_py)?;
    Ok(Scanner::new(reader, size_hint, max_span_lines))
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

fn group_text(hay: &[u8], caps: &Captures, index: usize) -> Option<String> {
    caps.get_group(index)
        .map(|span| String::from_utf8_lossy(&hay[span.range()]).into_owned())
}

fn build_match(compiled: &Compiled, caps: &Captures, hay: &[u8], span: (usize, usize)) -> Match {
    Match {
        groups: (1..caps.group_len())
            .map(|i| group_text(hay, caps, i))
            .collect(),
        named_groups: compiled
            .names
            .iter()
            .map(|(name, i)| (name.clone(), group_text(hay, caps, *i)))
            .collect(),
        start: span.0,
        end: span.1,
        match_str: group_text(hay, caps, 0).unwrap_or_default(),
    }
}

fn search_impl(
    py: Python<'_>,
    compiled: &Compiled,
    file_path: &str,
    max_span_lines: Option<usize>,
    anchored: bool,
) -> PyResult<Option<Match>> {
    py.detach(|| {
        let mut scanner = open_scanner(file_path, max_span_lines)?;
        let mut caps = compiled.re.create_captures();
        let found = if anchored {
            scanner.match_start(&compiled.re, &mut caps)
        } else {
            scanner.next(&compiled.re, &mut caps)
        }
        .map_err(io_to_py)?;
        Ok(found.map(|span| build_match(compiled, &caps, scanner.hay(), span)))
    })
}

fn findall_impl(
    py: Python<'_>,
    compiled: &Compiled,
    file_path: &str,
    max_span_lines: Option<usize>,
) -> PyResult<Vec<Vec<Option<String>>>> {
    py.detach(|| {
        let mut scanner = open_scanner(file_path, max_span_lines)?;
        let mut caps = compiled.re.create_captures();
        let mut out = Vec::new();
        while scanner
            .next(&compiled.re, &mut caps)
            .map_err(io_to_py)?
            .is_some()
        {
            let hay = scanner.hay();
            out.push(
                (0..caps.group_len())
                    .map(|i| group_text(hay, &caps, i))
                    .collect(),
            );
        }
        Ok(out)
    })
}

#[pyclass(unsendable)]
struct MatchIter {
    compiled: Arc<Compiled>,
    scanner: Scanner,
    caps: Captures,
}

#[pymethods]
impl MatchIter {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self, py: Python<'_>) -> PyResult<Option<Match>> {
        let compiled = self.compiled.clone();
        let scanner = &mut self.scanner;
        let caps = &mut self.caps;
        py.detach(|| {
            let found = scanner.next(&compiled.re, caps).map_err(io_to_py)?;
            Ok(found.map(|span| build_match(&compiled, caps, scanner.hay(), span)))
        })
    }
}

fn finditer_impl(
    py: Python<'_>,
    compiled: Arc<Compiled>,
    file_path: &str,
    max_span_lines: Option<usize>,
) -> PyResult<Py<MatchIter>> {
    let scanner = open_scanner(file_path, max_span_lines)?;
    let caps = compiled.re.create_captures();
    Py::new(
        py,
        MatchIter {
            compiled,
            scanner,
            caps,
        },
    )
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
    let compiled = build_regex(regex, flags)?;
    search_impl(py, &compiled, file_path, max_span_lines, false)
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
    let compiled = build_regex(regex, flags)?;
    search_impl(py, &compiled, file_path, max_span_lines, true)
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
    let compiled = build_regex(regex, flags)?;
    findall_impl(py, &compiled, file_path, max_span_lines)
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
    let compiled = Arc::new(build_regex(regex, flags)?);
    finditer_impl(py, compiled, file_path, max_span_lines)
}

/// Test hook: set how many bytes scanners created from now on read per
/// refill. Returns the previous value. Results never depend on this.
#[pyfunction]
fn _set_block_size(size: usize) -> usize {
    scanner::BLOCK_SIZE.swap(size.max(1), Ordering::Relaxed)
}

#[pyclass]
struct Pattern {
    compiled: Arc<Compiled>,
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
        Ok(Self {
            compiled: Arc::new(build_regex(pattern, flags)?),
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
        search_impl(py, &self.compiled, file_path, max_span_lines, false)
    }

    #[pyo3(name = "match", signature = (file_path, max_span_lines=None))]
    fn match_(
        &self,
        py: Python<'_>,
        file_path: &str,
        max_span_lines: Option<usize>,
    ) -> PyResult<Option<Match>> {
        search_impl(py, &self.compiled, file_path, max_span_lines, true)
    }

    #[pyo3(signature = (file_path, max_span_lines=None))]
    fn findall(
        &self,
        py: Python<'_>,
        file_path: &str,
        max_span_lines: Option<usize>,
    ) -> PyResult<Vec<Vec<Option<String>>>> {
        findall_impl(py, &self.compiled, file_path, max_span_lines)
    }

    #[pyo3(signature = (file_path, max_span_lines=None))]
    fn finditer(
        &self,
        py: Python<'_>,
        file_path: &str,
        max_span_lines: Option<usize>,
    ) -> PyResult<Py<MatchIter>> {
        finditer_impl(py, self.compiled.clone(), file_path, max_span_lines)
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
    m.add_function(wrap_pyfunction!(_set_block_size, m)?)?;
    m.add_class::<Match>()?;
    m.add_class::<Pattern>()?;
    m.add_class::<MatchIter>()?;
    Ok(())
}
