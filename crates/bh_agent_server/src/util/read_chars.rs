use std::fs::File;
use std::io::Read;

use anyhow::Result;
use log::trace;
use unicode_reader::Graphemes;

use bh_agent_common::FileOpenType;

pub fn read_generic(file: &mut File, n: Option<u32>, file_type: FileOpenType) -> Result<Vec<u8>> {
    trace!("Entering read_generic");
    if let Some(num_bytes) = n {
        match file_type {
            FileOpenType::Binary => Ok(read_bytes(file, num_bytes as usize)?),
            FileOpenType::Text => Ok(read_graphemes(file, num_bytes as usize)?),
        }
    } else {
        // if n is None, we just read the whole file, text parsing happens on the client
        Ok(file.bytes().collect::<Result<Vec<u8>, std::io::Error>>()?)
    }
}

fn read_bytes(file: &mut File, n: usize) -> Result<Vec<u8>> {
    Ok(file.bytes().take(n).collect::<Result<Vec<u8>, std::io::Error>>()?)
}

fn read_graphemes(file: &mut File, n: usize) -> Result<Vec<u8>> {
    Ok(Graphemes::from(file)
        .take(n)
        .into_iter()
        .collect::<Result<Vec<String>, std::io::Error>>()?
        .join("")
        .as_bytes()
        .to_vec()
    )
}
