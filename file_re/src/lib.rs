use pyo3::prelude::*;
use regex::Regex;
use std::collections::{HashMap, VecDeque};
mod read_file;
use std::io::BufRead;

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
fn _search_num_lines(regex: &str, file_path: &str, num_lines: i32) -> PyResult<Option<Match>> {
    if num_lines <= 0 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "num_lines must be greater than 0"
        ));
    }
    let num_lines = num_lines as usize;

    let re = Regex::new(regex)
        .map_err(|err| PyErr::new::<pyo3::exceptions::PyValueError, _>(err.to_string()))?;

    let reader = read_file::open_file_as_reader(file_path)?;
    
    let mut line_buffer: VecDeque<String> = VecDeque::new();
    let mut line_positions: VecDeque<usize> = VecDeque::new();
    let mut current_position = 0;
    let mut best_match: Option<Match> = None;
    let mut first_match_found = false;
    let mut lines_iter = reader.lines();

    // Process lines until we find the first match or reach end of file
    while let Some(line_result) = lines_iter.next() {
        let line = line_result.unwrap();
        
        // Add current line to buffer
        line_buffer.push_back(line.clone());
        line_positions.push_back(current_position);
        
        // Remove oldest line if buffer exceeds num_lines
        if line_buffer.len() > num_lines {
            line_buffer.pop_front();
            line_positions.pop_front();
        }
        
        // Try to match when buffer has at least one line
        if !line_buffer.is_empty() {
            let buffer_text = line_buffer.iter()
                .map(|s| s.as_str())
                .collect::<Vec<&str>>()
                .join("\n");
            
            if let Some(captures) = re.captures(&buffer_text) {
                let mat = captures.get(0).unwrap();
                let match_str = mat.as_str().to_string();
                
                let start_byte = mat.start();
                let end_byte = mat.end();
                
                let start_char = buffer_text[..start_byte].chars().count();
                let end_char = buffer_text[..end_byte].chars().count();
                
                // Calculate absolute positions
                let buffer_start_pos = *line_positions.front().unwrap();
                let absolute_start = buffer_start_pos + start_char;
                let absolute_end = buffer_start_pos + end_char;
                
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
                
                let current_match = Match {
                    groups,
                    named_groups,
                    start: absolute_start,
                    end: absolute_end,
                    match_str,
                };
                
                // First match found - set it as best match
                best_match = Some(current_match);
                first_match_found = true;
                break;
            }
        }
        
        current_position += line.chars().count() + 1; // +1 for newline
    }

    // If first match found, continue checking exactly num_lines more times
    if first_match_found {
        for _ in 0..num_lines {
            if let Some(line_result) = lines_iter.next() {
                let line = line_result.unwrap();
                
                // Add current line to buffer
                line_buffer.push_back(line.clone());
                line_positions.push_back(current_position);
                
                // Remove oldest line if buffer exceeds num_lines
                if line_buffer.len() > num_lines {
                    line_buffer.pop_front();
                    line_positions.pop_front();
                }
                
                // Try to match
                let buffer_text = line_buffer.iter()
                    .map(|s| s.as_str())
                    .collect::<Vec<&str>>()
                    .join("\n");
                
                if let Some(captures) = re.captures(&buffer_text) {
                    let mat = captures.get(0).unwrap();
                    let match_str = mat.as_str().to_string();
                    
                    let start_byte = mat.start();
                    let end_byte = mat.end();
                    
                    let start_char = buffer_text[..start_byte].chars().count();
                    let end_char = buffer_text[..end_byte].chars().count();
                    
                    // Calculate absolute positions
                    let buffer_start_pos = *line_positions.front().unwrap();
                    let absolute_start = buffer_start_pos + start_char;
                    let absolute_end = buffer_start_pos + end_char;
                    
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
                    
                    let current_match = Match {
                        groups,
                        named_groups,
                        start: absolute_start,
                        end: absolute_end,
                        match_str,
                    };
                    
                    // Update to the bigger match (by end position, which represents longer match)
                    if let Some(ref existing_match) = best_match {
                        if current_match.end > existing_match.end {
                            best_match = Some(current_match);
                        }
                    } else {
                        best_match = Some(current_match);
                    }
                }
                
                current_position += line.chars().count() + 1; // +1 for newline
            } else {
                // No more lines in file
                break;
            }
        }
    }
    
    Ok(best_match)

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
fn _findall_num_lines(regex: &str, file_path: &str, num_lines: i32) -> PyResult<Vec<Vec<String>>> {
    if num_lines <= 0 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "num_lines must be greater than 0"
        ));
    }
    let num_lines = num_lines as usize;

    let re = Regex::new(regex)
        .map_err(|err| PyErr::new::<pyo3::exceptions::PyValueError, _>(err.to_string()))?;

    let reader = read_file::open_file_as_reader(file_path)?;
    
    let mut line_buffer: VecDeque<String> = VecDeque::new();
    let mut matches: Vec<Vec<String>> = Vec::new();

    for line in reader.lines() {
        let line = line.unwrap();
        
        // Add current line to buffer
        line_buffer.push_back(line.clone());
        
        // Remove oldest line if buffer exceeds num_lines
        if line_buffer.len() > num_lines {
            line_buffer.pop_front();
        }
        
        // Try to match when buffer has at least one line
        if !line_buffer.is_empty() {
            let buffer_text = line_buffer.iter()
                .map(|s| s.as_str())
                .collect::<Vec<&str>>()
                .join("\n");
            
            for caps in re.captures_iter(&buffer_text) {
                let groups: Vec<String> = (0..caps.len())
                    .map(|i| caps.get(i).map_or(String::new(), |m| m.as_str().to_string()))
                    .collect();
                matches.push(groups);
            }
        }
    }
    
    Ok(matches)
}

#[pymodule]
#[pyo3(name="_file_re")]
fn file_re(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(_search_single_line, m)?)?;
    m.add_function(wrap_pyfunction!(_search_multi_line, m)?)?;
    m.add_function(wrap_pyfunction!(_search_num_lines, m)?)?;
    m.add_function(wrap_pyfunction!(_findall_single_line, m)?)?;
    m.add_function(wrap_pyfunction!(_findall_multi_line, m)?)?;
    m.add_function(wrap_pyfunction!(_findall_num_lines, m)?)?;
    m.add_class::<Match>()?;
    Ok(())
}