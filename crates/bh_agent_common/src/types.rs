#[cfg(feature = "python")]
use pyo3::pyclass;
use serde::{Deserialize, Serialize};

pub type EnvironmentId = u64;
pub type ProcessId = u64;
pub type FileId = u64;

#[derive(Copy, Clone, Debug, Serialize, Deserialize)]
pub enum ProcessChannel {
    Stdin,
    Stdout,
    Stderr,
}

#[derive(Copy, Clone, Debug, Default, Serialize, Deserialize)]
pub enum Redirection {
    #[default]
    None,
    Save,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct RemotePOpenConfig {
    pub argv: Vec<String>,
    pub stdin: Redirection,
    pub stdout: Redirection,
    pub stderr: Redirection,
    pub executable: Option<String>,
    pub env: Option<Vec<(String, String)>>,
    pub cwd: Option<String>,
    pub setuid: Option<u32>,
    pub setgid: Option<u32>,
    pub setpgid: bool,
}

#[derive(Copy, Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum FileOpenMode {
    Read,
    Write,
    ExclusiveWrite,
    Append,
    Update,
}

#[derive(Copy, Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum FileOpenType {
    Binary,
    Text,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum UserId {
    Id(u32),
    Name(String),
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[cfg_attr(feature = "python", pyclass(get_all))]
pub struct FileStat {
    pub mode: u16,
    pub uid: u32,
    pub gid: u32,
    pub size: i64,
    pub atime: i64,
    pub mtime: i64,
    pub ctime: i64,
}

#[cfg(target_family = "unix")]
impl From<nix::sys::stat::FileStat> for FileStat {
    fn from(stat: nix::sys::stat::FileStat) -> Self {
        Self {
            mode: stat.st_mode as u16,
            uid: stat.st_uid,
            gid: stat.st_gid,
            size: stat.st_size as i64,
            atime: stat.st_atime as i64,
            mtime: stat.st_mtime as i64,
            ctime: stat.st_ctime as i64,
        }
    }
}
