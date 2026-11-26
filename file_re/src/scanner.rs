//! Chunked file scanner.
//!
//! The file is read in large blocks. Each block is cut at its last line
//! boundary, normalised (`\r\n` -> `\n`), validated as UTF-8 and searched in
//! place, so the regex engine's SIMD prefilters run over big buffers instead
//! of one line at a time.
//!
//! # Semantics of `max_lines`
//!
//! Matches are reported left to right and never overlap. With
//! `max_lines = Some(n)` a match may touch at most `n` consecutive lines: if
//! it starts on line `L` it must end before the line terminator of line
//! `L + n - 1`. The next match is the one a regex search restricted to that
//! range would return for the smallest start position that has any such
//! match. Anchors and word boundaries always see the real file: `\A` only
//! matches at the start of the file and `\z` only at its end, whatever the
//! window is.
//!
//! The result is independent of where block boundaries fall.

use memchr::{memchr, memchr_iter, memmem, memrchr, memrchr_iter};
use regex_automata::{meta::Regex, util::captures::Captures, Anchored, Input, Match};
use std::io::{self, Read};
use std::sync::atomic::{AtomicUsize, Ordering};

/// Bytes requested from the reader per refill.
pub static BLOCK_SIZE: AtomicUsize = AtomicUsize::new(256 * 1024);

/// After this many matches that were too long for the window, stop trying
/// the whole buffer first and search window by window instead. This bounds
/// the cost of patterns such as `(?s)BEGIN.*END` whose unrestricted match
/// runs to the end of every block.
const OVERSIZE_LIMIT: u32 = 32;

pub struct Scanner {
    reader: Box<dyn Read + Send>,
    size_hint: Option<u64>,
    buf: Vec<u8>,
    /// `buf[..ready]` is normalised, valid UTF-8 and ends on a line boundary
    /// (or at end of file). `buf[ready..]` is a partial line.
    ready: usize,
    eof: bool,
    max_lines: Option<usize>,
    /// Next search start, as an offset into `buf`.
    pos: usize,
    /// Match starts below this offset can be decided with the data loaded.
    commit_end: usize,
    /// `cur_char` is the absolute character offset of `buf[cur_byte]`.
    cur_byte: usize,
    cur_char: usize,
    oversize: u32,
    block: usize,
}

fn count_chars(bytes: &[u8]) -> usize {
    // SIMD count of bytes that are not UTF-8 continuation bytes.
    bytecount::num_chars(bytes)
}

/// Rewrite `\r\n` as `\n` in `buf[from..to]`, shifting the tail down.
/// Returns the new end of the region.
fn normalize_crlf(buf: &mut Vec<u8>, from: usize, to: usize) -> usize {
    let Some(first) = memmem::find(&buf[from..to], b"\r\n") else {
        return to;
    };
    let mut w = from + first;
    let mut r = w;
    while r < to {
        if buf[r] == b'\r' && r + 1 < to && buf[r + 1] == b'\n' {
            r += 1;
            continue;
        }
        buf[w] = buf[r];
        w += 1;
        r += 1;
    }
    let len = buf.len();
    buf.copy_within(to..len, w);
    buf.truncate(len - (to - w));
    w
}

impl Scanner {
    pub fn new(
        reader: Box<dyn Read + Send>,
        size_hint: Option<u64>,
        max_lines: Option<usize>,
    ) -> Self {
        Self {
            reader,
            size_hint,
            buf: Vec::new(),
            ready: 0,
            eof: false,
            max_lines,
            pos: 0,
            commit_end: 0,
            cur_byte: 0,
            cur_char: 0,
            oversize: 0,
            block: BLOCK_SIZE.load(Ordering::Relaxed).max(1),
        }
    }

    /// The searchable text that capture spans refer to.
    pub fn hay(&self) -> &[u8] {
        &self.buf[..self.ready]
    }

    /// Drop everything before the search position, keeping one character of
    /// look-behind so `\b`, `^` and `\A` still see what precedes it.
    fn compact(&mut self) {
        let mut keep = self.pos.min(self.ready).saturating_sub(1);
        while keep > 0 && (self.buf[keep] & 0xC0) == 0x80 {
            keep -= 1;
        }
        if keep == 0 {
            return;
        }
        if self.cur_byte < keep {
            self.cur_char += count_chars(&self.buf[self.cur_byte..keep]);
            self.cur_byte = keep;
        }
        self.buf.drain(..keep);
        self.ready -= keep;
        self.pos -= keep;
        self.cur_byte -= keep;
        self.commit_end = self.commit_end.saturating_sub(keep);
    }

    fn fill(&mut self) -> io::Result<()> {
        self.compact();
        let before = self.buf.len();
        if self.max_lines.is_none() {
            // Size the buffer once instead of growing it; if the size does
            // not fit in memory, report it rather than abort.
            if let Some(size) = self.size_hint.and_then(|s| usize::try_from(s).ok()) {
                self.buf
                    .try_reserve(size.saturating_add(1))
                    .map_err(|e| io::Error::new(io::ErrorKind::OutOfMemory, e))?;
            }
            self.reader.read_to_end(&mut self.buf)?;
            self.eof = true;
        } else {
            let n = self
                .reader
                .by_ref()
                .take(self.block as u64)
                .read_to_end(&mut self.buf)?;
            if n == 0 {
                self.eof = true;
            }
        }
        let region_end = if self.eof {
            self.buf.len()
        } else {
            // buf[ready..before] holds no newline, so only look at new bytes.
            match memrchr(b'\n', &self.buf[before..]) {
                Some(i) => before + i + 1,
                None => return Ok(()),
            }
        };
        let region_end = normalize_crlf(&mut self.buf, self.ready, region_end);
        if std::str::from_utf8(&self.buf[self.ready..region_end]).is_err() {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "stream did not contain valid UTF-8",
            ));
        }
        self.ready = region_end;
        self.commit_end = if self.eof {
            self.ready + 1
        } else {
            // A start on line L is decidable once line L + n - 1 is complete,
            // so the last n - 1 complete lines have to wait for more data.
            let n = self.max_lines.unwrap_or(1);
            memrchr_iter(b'\n', &self.buf[..self.ready])
                .nth(n - 1)
                .map_or(0, |i| i + 1)
        };
        Ok(())
    }

    fn accept(&mut self, m: Match) -> (usize, usize) {
        let (s, e) = (m.start(), m.end());
        let cs = self.cur_char + count_chars(&self.buf[self.cur_byte..s]);
        let ce = cs + count_chars(&self.buf[s..e]);
        self.cur_byte = e;
        self.cur_char = ce;
        self.pos = if e > s {
            e
        } else {
            // Step over one character after an empty match.
            let mut p = e + 1;
            while p < self.ready && (self.buf[p] & 0xC0) == 0x80 {
                p += 1;
            }
            p
        };
        (cs, ce)
    }

    /// Find the next match. On success `caps` holds byte spans into
    /// [`Scanner::hay`], valid until the next call, and the returned pair is
    /// the match's absolute `(start, end)` in characters.
    pub fn next(&mut self, re: &Regex, caps: &mut Captures) -> io::Result<Option<(usize, usize)>> {
        loop {
            if self.pos >= self.commit_end {
                if self.eof {
                    return Ok(None);
                }
                self.fill()?;
                continue;
            }
            let hay = &self.buf[..self.ready];
            let mut start = self.pos;
            if self.oversize < OVERSIZE_LIMIT {
                // Fast path: search everything loaded in one call.
                re.search_captures(&Input::new(hay).range(self.pos..), caps);
                let Some(m) = caps.get_match() else {
                    self.pos = self.commit_end;
                    continue;
                };
                if m.start() >= self.commit_end {
                    self.pos = self.commit_end;
                    continue;
                }
                let fits = match self.max_lines {
                    None => true,
                    Some(n) => memchr_iter(b'\n', &hay[m.range()]).nth(n - 1).is_none(),
                };
                if fits {
                    return Ok(Some(self.accept(m)));
                }
                // Too long for the window. A shorter match may still start on
                // the same line, so retry restricted to that line's window.
                self.oversize += 1;
                start = m.start();
            }
            let n = self.max_lines.unwrap_or(1);
            let line_end = memchr(b'\n', &hay[start..]).map_or(hay.len(), |i| start + i);
            let limit = memchr_iter(b'\n', &hay[start..])
                .nth(n - 1)
                .map_or(hay.len(), |i| start + i);
            re.search_captures(&Input::new(hay).range(start..limit), caps);
            if let Some(m) = caps.get_match() {
                if m.start() <= line_end {
                    return Ok(Some(self.accept(m)));
                }
            }
            // Nothing starts on this line; later lines get their own window.
            self.pos = line_end + 1;
        }
    }

    /// Match anchored at the very start of the file. Only valid on a fresh
    /// scanner.
    pub fn match_start(
        &mut self,
        re: &Regex,
        caps: &mut Captures,
    ) -> io::Result<Option<(usize, usize)>> {
        while self.commit_end == 0 && !self.eof {
            self.fill()?;
        }
        let hay = &self.buf[..self.ready];
        let limit = match self.max_lines {
            None => hay.len(),
            Some(n) => memchr_iter(b'\n', hay).nth(n - 1).unwrap_or(hay.len()),
        };
        let input = Input::new(hay).range(..limit).anchored(Anchored::Yes);
        re.search_captures(&input, caps);
        Ok(caps.get_match().map(|m| self.accept(m)))
    }
}
