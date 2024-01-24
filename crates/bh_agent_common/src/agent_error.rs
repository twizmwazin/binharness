use crate::AgentError::LockError;
use serde::{Deserialize, Serialize};
use std::sync::{PoisonError, RwLockReadGuard, RwLockWriteGuard};
use thiserror::Error;

#[derive(Error, Debug, Serialize, Deserialize)]
pub enum AgentError {
    #[error("Invalid environment ID")]
    InvalidEnvironmentId,
    #[error("IO Error: {0}")]
    IoError(String),
    #[error("Invalid file ID")]
    InvalidFileDescriptor,
    #[error("Invalid seek whence")]
    InvalidSeekWhence,
    #[error("Lock Error")]
    LockError,
    #[error("Failed to start process: {0}")]
    ProcessStartFailure(String),
    #[error("Invalid process ID")]
    InvalidProcessId,
    #[error("Process channel not piped")]
    ProcessChannelNotPiped,
    #[error("User {0} not found")]
    UserNotFound(String),
    #[error("Group {0} not found")]
    GroupNotFound(String),
    #[error("Unix Error: {0}")]
    Errno(i32),
    #[error("Unsupported platform")]
    UnsupportedPlatform,
    #[error("The server state is inconsistent")]
    Inconsistent,
    #[error("Unknown Error")]
    Unknown,
}

impl<T> From<PoisonError<T>> for AgentError {
    fn from(_: PoisonError<T>) -> Self {
        LockError
    }
}

impl<T> From<RwLockReadGuard<'_, T>> for AgentError {
    fn from(_: RwLockReadGuard<T>) -> Self {
        LockError
    }
}

impl<T> From<RwLockWriteGuard<'_, T>> for AgentError {
    fn from(_: RwLockWriteGuard<T>) -> Self {
        LockError
    }
}

#[cfg(target_family = "unix")]
impl From<nix::errno::Errno> for AgentError {
    fn from(errno: nix::errno::Errno) -> Self {
        AgentError::Errno(errno as i32)
    }
}

impl From<std::io::Error> for AgentError {
    fn from(error: std::io::Error) -> Self {
        AgentError::IoError(error.to_string())
    }
}
