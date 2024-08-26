use pyo3::prelude::*;
use std::path::Path;
use regex::Regex;
use std::fs;
use std::collections::HashMap;
mod read_file;
use std::io::{self, BufRead, Read, BufReader};
use std::fs::File;
use flate2::read::GzDecoder;

// A struct to represent a regex match similar to Python's re match object
#[pyclass]
struct Match {
    start: usize,
    end: usize,
    
}

#[pymethods]
impl Match {
    
    fn start(&self) -> usize {
        self.start
    }

    fn end(&self) -> usize {
        self.end
    }

    fn span(&self) -> (usize, usize) {
        (self.start, self.end)
    }
}

#[pyfunction]
fn search_line_by_line(regex: &str, file_path: &str) -> PyResult<Option<Match>> {
    let re = Regex::new(regex)
        .map_err(|err| PyErr::new::<pyo3::exceptions::PyValueError, _>(err.to_string()))?;

    let reader = read_file::open_file_as_reader(file_path)?;

    let mut actual_start = 0;

    for line in reader.lines() {
        let line = line.unwrap();

        if let Some(mat) = re.find(&line) {
            let start_byte = mat.start();
            let end_byte = mat.end();

            let start_char = line[..start_byte].chars().count();
            let end_char = line[..end_byte].chars().count();
            
            return Ok(Some(Match {
                start: actual_start + start_char,
                end: actual_start + end_char,
            }));
        }
        actual_start += line.chars().count() + 1;
    }

    Ok(None)

}

fn read_file(path: &str) -> io::Result<String> {
    let file = File::open(path)?;
    let mut buf_reader = BufReader::new(GzDecoder::new(file));
    let mut content = String::new();
    buf_reader.read_to_string(&mut content)?;
    Ok(content)
}


fn search_rust(re: &Regex, path: &str) -> Result<(usize, usize), io::Error> {
    let content = read_file(path)?;
    if let Some(mat) = re.find(&content) {
        let start_char_pos = content[..mat.start()].chars().count();
        let end_char_pos = content[..mat.end()].chars().count();
        Ok((start_char_pos, end_char_pos))
    } else {
        Err(io::Error::new(io::ErrorKind::Other, "No match found"))
    }
}

#[pyfunction]
fn search_full_file(regex: &str, file_path: &str) -> PyResult<Option<Match>> {
    // Compile the regex pattern
    pyo3::prepare_freethreaded_python();
    let re = Regex::new(regex)
        .map_err(|err| PyErr::new::<pyo3::exceptions::PyValueError, _>(err.to_string()))?;
    
    let result = search_rust(&re, file_path);

    match result {
        Ok((start, end)) => Ok(Some(Match { start, end })),
         Err(_) => Ok(None),
    }

}

// A Python module implemented in Rust.
#[pymodule]
fn file_re(m: &Bound<'_, PyModule>) -> PyResult<()> {
    
    m.add_function(wrap_pyfunction!(search_line_by_line, m)?)?;
    m.add_function(wrap_pyfunction!(search_full_file, m)?)?;
    m.add_class::<Match>()?;
    Ok(())
}
