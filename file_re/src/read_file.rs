use std::fs::File;
use std::io::{self, BufReader, BufRead};
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

