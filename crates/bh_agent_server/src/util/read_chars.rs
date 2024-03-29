use std::fs::File;
use std::io::Read;

use anyhow::Result;
use log::trace;
use unicode_reader::Graphemes;

use bh_agent_common::FileOpenType;

#[cfg(target_family = "unix")]
use crate::util::is_blocking;

// This is uhhh... a bit messy. The error handling is the main issue that is
//necessitating this inner function.
pub fn read_generic(
    file: &mut File,
    mut n: Option<u32>,
    file_type: FileOpenType,
) -> Result<Vec<u8>> {
    trace!("Entering read_generic");

    #[cfg(target_family = "unix")]
    if n.is_none() && !is_blocking(file)? {
        n = Some(1024_u32.pow(2));
    }

    let inner: Result<Vec<u8>> = (|| {
        trace!("read_generic: entering inner closure...");
        if let Some(num_bytes) = n {
            match file_type {
                FileOpenType::Binary => Ok(read_bytes(file, num_bytes as usize)?),
                FileOpenType::Text => Ok(read_graphemes(file, num_bytes as usize)?),
            }
        } else {
            // if n is None, we just read the whole file, text parsing happens on the client
            Ok(file.bytes().collect::<Result<Vec<u8>, std::io::Error>>()?)
        }
    })();
    trace!("read_generic: processing inner result...");
    inner.or_else(|e| {
        if let Some(std::io::ErrorKind::WouldBlock) =
            e.downcast_ref::<std::io::Error>().map(|e| e.kind())
        {
            trace!("read_generic: WouldBlock error, returning empty vec");
            Ok(Vec::new())
        } else {
            trace!("read_generic: returning error");
            Err(e)
        }
    })
}

fn read_bytes(file: &mut File, n: usize) -> Result<Vec<u8>> {
    Ok(file
        .bytes()
        .take(n)
        .collect::<Result<Vec<u8>, std::io::Error>>()?)
}

fn read_graphemes(file: &mut File, n: usize) -> Result<Vec<u8>> {
    Ok(Graphemes::from(file)
        .take(n)
        .into_iter()
        .collect::<Result<Vec<String>, std::io::Error>>()?
        .join("")
        .as_bytes()
        .to_vec())
}
