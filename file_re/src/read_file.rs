use std::fs::File;
use std::io::{self, BufReader, BufRead, Read};
use flate2::read::GzDecoder;
use xz2::read::XzDecoder;


enum FileType {
    Normal,
    Gz,
    Xz,
}

fn detect_file_type(file_path: &str) -> io::Result<FileType> {
    if file_path.ends_with(".gz") {
        Ok(FileType::Gz)
    } else if file_path.ends_with(".xz") {
        Ok(FileType::Xz)
    } else {
        Ok(FileType::Normal)
    }
}

fn read_txt(path: &str) -> io::Result<String> {
    let mut file = File::open(path)?;
    let mut content = String::new();
    file.read_to_string(&mut content)?;

    #[cfg(windows)]
    {
        content = content.replace("\r\n", "\n");
    }
    
    Ok(content)
}

fn read_xz(path: &str) -> io::Result<String> {
    let file = File::open(path)?;
    let mut buf_reader = BufReader::new(XzDecoder::new(file));
    let mut content = String::new();
    buf_reader.read_to_string(&mut content)?;
    Ok(content)
}

fn read_gz(path: &str) -> io::Result<String> {
    let file = File::open(path)?;
    let mut buf_reader = BufReader::new(GzDecoder::new(file));
    let mut content = String::new();
    buf_reader.read_to_string(&mut content)?;
    Ok(content)
}


pub fn open_file_full_content(file_path: &str) -> io::Result<String> {
    let file_type = detect_file_type(file_path)?;
    match file_type {
        FileType::Normal => read_txt(file_path),
        FileType::Gz => read_gz(file_path),
        FileType::Xz => read_xz(file_path),
    }
}


pub fn open_file_as_reader(file_path: &str) -> io::Result<Box<dyn BufRead>> {
    let file = File::open(file_path)?;
    let file_type = detect_file_type(file_path)?;

    let reader: Box<dyn BufRead> = match file_type {
        FileType::Normal => Box::new(BufReader::new(file)),
        FileType::Gz => Box::new(BufReader::new(GzDecoder::new(file))),
        FileType::Xz => Box::new(BufReader::new(XzDecoder::new(file))),
    };

    Ok(reader)
}

