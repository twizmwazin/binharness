mod read_chars;
mod read_lines;
#[cfg(target_family = "unix")]
mod unix_functions;

pub use read_chars::*;
pub use read_lines::read_lines;
#[cfg(target_family = "unix")]
pub use unix_functions::{chmod, chown};
