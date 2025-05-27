use pyo3::prelude::*;
use regex::Regex;
use std::collections::{HashMap, VecDeque};
mod read_file;
use std::io::{BufRead};

#[pyclass]
struct Match {
    groups: Vec<String>,
    named_groups: HashMap<String, String>,
    start: usize,
    end: usize,
    match_str: String,
}

#[pymethods]
impl Match {
    
    #[getter]
    fn groups(&self) -> Vec<String> {
        self.groups.clone()
    }

    #[getter]
    fn named_groups(&self) -> HashMap<String, String> {
        self.named_groups.clone()
    }

    #[getter]
    fn start(&self) -> usize {
        self.start
    }

    #[getter]
    fn end(&self) -> usize {
        self.end
    }

    #[getter]
    fn match_str(&self) -> String {
        self.match_str.clone()
    }

}

#[pyfunction]
fn _search_single_line(regex: &str, file_path: &str) -> PyResult<Option<Match>> {
    let re = Regex::new(regex)
        .map_err(|err| PyErr::new::<pyo3::exceptions::PyValueError, _>(err.to_string()))?;

    let reader = read_file::open_file_as_reader(file_path)?;

    let mut actual_start = 0;

    for line in reader.lines() {
        let line = line.unwrap();

        if let Some(captures) = re.captures(&line) {
            let mat = captures.get(0).unwrap();

            let match_str = mat.as_str().to_string();

            let start_byte = mat.start();
            let end_byte = mat.end();

            let start_char = line[..start_byte].chars().count();
            let end_char = line[..end_byte].chars().count();

            let mut named_groups: HashMap<String, String> = HashMap::new();

            let groups: Vec<String> = (1..captures.len())
                .map(|i| captures.get(i).map_or(String::new(), |m| m.as_str().to_string()))
                .collect();

            for name in re.capture_names().flatten() {
                if let Some(m) = captures.name(name) {
                    named_groups.insert(name.to_string(), m.as_str().to_string());
                } else {
                    named_groups.insert(name.to_string(), String::new());
                }
            }

            return Ok(Some(Match {
                groups,
                named_groups,
                start: actual_start + start_char,
                end: actual_start + end_char,
                match_str,
            }));
        }
        actual_start += line.chars().count() + 1;
    }

    Ok(None)
}

#[pyfunction]
fn _search_multi_line(regex: &str, file_path: &str) -> PyResult<Option<Match>> {
    let re = Regex::new(regex)
        .map_err(|err| PyErr::new::<pyo3::exceptions::PyValueError, _>(err.to_string()))?;

    let file_content = read_file::open_file_full_content(file_path)?;

    if let Some(captures) = re.captures(&file_content) {
        let mat = captures.get(0).unwrap();
        let match_str = mat.as_str().to_string();

        let start_byte = mat.start();
        let end_byte = mat.end();

        let start_char = file_content[..start_byte].chars().count();
        let end_char = file_content[..end_byte].chars().count();

        let mut named_groups: HashMap<String, String> = HashMap::new();
        let groups: Vec<String> = (1..captures.len())
            .map(|i| captures.get(i).map_or(String::new(), |m| m.as_str().to_string()))
            .collect();

        for name in re.capture_names().flatten() {
            if let Some(m) = captures.name(name) {
                named_groups.insert(name.to_string(), m.as_str().to_string());
            } else {
                named_groups.insert(name.to_string(), String::new());
            }
        }

        return Ok(Some(Match {
            groups,
            named_groups,
            start: start_char,
            end: end_char,
            match_str,
        }));
    }

    Ok(None)
}


#[pyfunction]
fn _findall_single_line(regex: &str, file_path: &str) -> PyResult<Vec<Vec<String>>> {
    let re = Regex::new(regex)
        .map_err(|err| PyErr::new::<pyo3::exceptions::PyValueError, _>(err.to_string()))?;

    let reader = read_file::open_file_as_reader(file_path)?;
    let mut matches: Vec<Vec<String>> = Vec::new();

    for line in reader.lines() {
        let line = line.unwrap();
        for caps in re.captures_iter(&line) {
            let groups: Vec<String> = (0..caps.len())
                .map(|i| caps.get(i).map_or(String::new(), |m| m.as_str().to_string()))
                .collect();
            matches.push(groups);
        }
    }
    
    Ok(matches)

}

#[pyfunction]
fn _findall_multi_line(regex: &str, path: &str) -> PyResult<Vec<Vec<String>>> {
    let re = Regex::new(regex)
        .map_err(|err| PyErr::new::<pyo3::exceptions::PyValueError, _>(err.to_string()))?;

    let file_content = read_file::open_file_full_content(path)?;

    let mut matches: Vec<Vec<String>> = Vec::new();

    for caps in re.captures_iter(&file_content) {
        let mut groups: Vec<String> = Vec::new();
        for group in caps.iter() {
            match group {
                Some(m) => groups.push(m.as_str().to_string()),
                None => groups.push(String::new()),
            }
        }
        matches.push(groups);
    }

    Ok(matches)
}

#[pyfunction]
fn _search_with_num_lines(regex: &str, file_path: &str, num_lines: usize) -> PyResult<Option<Match>> {
    if num_lines == 0 {
        return Ok(None);
    }

    let re = Regex::new(regex)
        .map_err(|err| PyErr::new::<pyo3::exceptions::PyValueError, _>(err.to_string()))?;

    let reader = read_file::open_file_as_reader(file_path)?;
    
    let mut line_queue: VecDeque<String> = VecDeque::new();
    let mut all_lines: Vec<String> = Vec::new();
    let mut last_match: Option<Match> = None;

    // First, collect all lines to handle offset calculation correctly
    for line in reader.lines() {
        let line = line.unwrap();
        all_lines.push(line);
    }

    // Now process with sliding window
    for i in 0..all_lines.len() {
        line_queue.push_back(all_lines[i].clone());
        
        if line_queue.len() > num_lines {
            line_queue.pop_front();
        }

        let combined_text = line_queue.iter()
            .map(|s| s.as_str())
            .collect::<Vec<&str>>()
            .join("\n");

        // Find the LAST match in this window, not the first
        let mut window_matches: Vec<_> = re.captures_iter(&combined_text).collect();
        if let Some(captures) = window_matches.pop() {  // Get the last match
            let mat = captures.get(0).unwrap();
            let match_str = mat.as_str().to_string();
            
            // Calculate the start of the current window in the file
            let window_start_line = if i + 1 >= num_lines { i + 1 - num_lines } else { 0 };
            let mut file_offset = 0;
            for j in 0..window_start_line {
                file_offset += all_lines[j].chars().count() + 1; // +1 for newline
            }
            
            let start_byte = mat.start();
            let end_byte = mat.end();
            
            let start_char = combined_text[..start_byte].chars().count();
            let end_char = combined_text[..end_byte].chars().count();
            
            let mut named_groups: HashMap<String, String> = HashMap::new();
            let groups: Vec<String> = (1..captures.len())
                .map(|i| captures.get(i).map_or(String::new(), |m| m.as_str().to_string()))
                .collect();

            for name in re.capture_names().flatten() {
                if let Some(m) = captures.name(name) {
                    named_groups.insert(name.to_string(), m.as_str().to_string());
                } else {
                    named_groups.insert(name.to_string(), String::new());
                }
            }

            last_match = Some(Match {
                groups,
                named_groups,
                start: file_offset + start_char,
                end: file_offset + end_char,
                match_str,
            });
        }
    }

    Ok(last_match)
}

#[pyfunction]
fn _findall_with_num_lines(regex: &str, file_path: &str, num_lines: usize) -> PyResult<Vec<Vec<String>>> {
    if num_lines == 0 {
        return Ok(Vec::new());
    }

    let re = Regex::new(regex)
        .map_err(|err| PyErr::new::<pyo3::exceptions::PyValueError, _>(err.to_string()))?;

    let reader = read_file::open_file_as_reader(file_path)?;
    
    let mut line_queue: VecDeque<String> = VecDeque::new();
    let mut all_matches: Vec<Vec<String>> = Vec::new();
    let mut processed_matches: std::collections::HashSet<String> = std::collections::HashSet::new();

    for line in reader.lines() {
        let line = line.unwrap();
        line_queue.push_back(line.clone());
        
        if line_queue.len() > num_lines {
            line_queue.pop_front();
        }

        let combined_text = line_queue.iter()
            .map(|s| s.as_str())
            .collect::<Vec<&str>>()
            .join("\n");

        for caps in re.captures_iter(&combined_text) {
            let match_key = format!("{}:{}", caps.get(0).unwrap().start(), caps.get(0).unwrap().as_str());
            
            if !processed_matches.contains(&match_key) {
                processed_matches.insert(match_key);
                
                let mut groups: Vec<String> = Vec::new();
                for group in caps.iter() {
                    match group {
                        Some(m) => groups.push(m.as_str().to_string()),
                        None => groups.push(String::new()),
                    }
                }
                all_matches.push(groups);
            }
        }
    }

    Ok(all_matches)
}


#[pymodule]
#[pyo3(name="_file_re")]
fn file_re(m: &Bound<'_, PyModule>) -> PyResult<()> {
    
    m.add_function(wrap_pyfunction!(_search_single_line, m)?)?;
    m.add_function(wrap_pyfunction!(_search_multi_line, m)?)?;
    m.add_function(wrap_pyfunction!(_findall_single_line, m)?)?;
    m.add_function(wrap_pyfunction!(_findall_multi_line, m)?)?;
    m.add_function(wrap_pyfunction!(_search_with_num_lines, m)?)?;
    m.add_function(wrap_pyfunction!(_findall_with_num_lines, m)?)?;
    m.add_class::<Match>()?;
    Ok(())
}

