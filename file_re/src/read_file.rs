use flate2::read::MultiGzDecoder;
use liblzma::read::XzDecoder;
use std::fs::File;
use std::io::{self, Read};
use std::path::Path;

/// Open `file_path` as a byte stream, transparently decoding `.gz` and `.xz`.
///
/// The second element is the on-disk size when it equals the decoded size
/// (plain files only); callers use it to pre-size buffers.
pub fn open(file_path: &str) -> io::Result<(Box<dyn Read + Send>, Option<u64>)> {
    let file = File::open(file_path)?;
    let extension = Path::new(file_path)
        .extension()
        .and_then(|ext| ext.to_str())
        .map(str::to_ascii_lowercase);
    match extension.as_deref() {
        // MultiGzDecoder also handles concatenated members (appended logs).
        Some("gz") => Ok((Box::new(MultiGzDecoder::new(file)), None)),
        Some("xz") => Ok((Box::new(XzDecoder::new_multi_decoder(file)), None)),
        _ => {
            let size = file.metadata().ok().map(|m| m.len());
            Ok((Box::new(file), size))
        }
    }
}
