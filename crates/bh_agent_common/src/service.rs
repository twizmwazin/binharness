use crate::agent_error::AgentError;
use crate::{
    EnvironmentId, FileId, FileOpenMode, FileOpenType, FileStat, ProcessChannel, ProcessId,
    RemotePOpenConfig, UserId,
};
use anyhow::Result;

#[tarpc::service]
pub trait BhAgentService {
    // Environment enumeration
    async fn get_environments() -> Vec<EnvironmentId>;

    async fn get_tempdir(env_id: EnvironmentId) -> Result<String, AgentError>;

    // Process management
    async fn run_command(
        env_id: EnvironmentId,
        config: RemotePOpenConfig,
    ) -> Result<ProcessId, AgentError>;

    async fn get_process_ids(env_id: EnvironmentId) -> Result<Vec<ProcessId>, AgentError>;

    async fn get_process_channel(
        env_id: EnvironmentId,
        proc_id: ProcessId,
        channel: ProcessChannel,
    ) -> Result<FileId, AgentError>;

    async fn process_poll(
        env_id: EnvironmentId,
        proc_id: ProcessId,
    ) -> Result<Option<u32>, AgentError>;

    async fn process_wait(
        env_id: EnvironmentId,
        proc_id: ProcessId,
        timeout: Option<u32>,
    ) -> Result<bool, AgentError>;

    async fn process_returncode(
        env_id: EnvironmentId,
        proc_id: ProcessId,
    ) -> Result<Option<u32>, AgentError>;

    // File IO
    // Implement most of the methods in binharness.IO, but omit ones that there can just be
    // replicated on the client side without a performance hit.
    // Data is represented as a Vec<u8> instead of a String because if we're in text mode, we can
    // just decode it on the client side. The server still needs to know the mode however, as an
    // N length read in text mode will be N chars, not N bytes.
    async fn file_open(
        env_id: EnvironmentId,
        path: String,
        mode: FileOpenMode,
        type_: FileOpenType,
    ) -> Result<FileId, AgentError>;

    async fn file_close(env_id: EnvironmentId, fd: FileId) -> Result<(), AgentError>;

    async fn file_is_closed(env_id: EnvironmentId, fd: FileId) -> Result<bool, AgentError>;

    async fn file_is_readable(env_id: EnvironmentId, fd: FileId) -> Result<bool, AgentError>;

    async fn file_read(
        env_id: EnvironmentId,
        fd: FileId,
        num_bytes: Option<u32>,
    ) -> Result<Vec<u8>, AgentError>;

    async fn file_read_lines(
        env_id: EnvironmentId,
        fd: FileId,
        hint: u32,
    ) -> Result<Vec<Vec<u8>>, AgentError>;

    async fn file_is_seekable(env_id: EnvironmentId, fd: FileId) -> Result<bool, AgentError>;

    async fn file_seek(
        env_id: EnvironmentId,
        fd: FileId,
        offset: i32,
        whence: i32,
    ) -> Result<(), AgentError>;

    async fn file_tell(env_id: EnvironmentId, fd: FileId) -> Result<i32, AgentError>;

    async fn file_is_writable(env_id: EnvironmentId, fd: FileId) -> Result<bool, AgentError>;

    async fn file_write(env_id: EnvironmentId, fd: FileId, data: Vec<u8>)
        -> Result<(), AgentError>;

    async fn file_set_blocking(
        env_id: EnvironmentId,
        fd: FileId,
        blocking: bool,
    ) -> Result<(), AgentError>;

    async fn chown(
        env_id: EnvironmentId,
        path: String,
        user: Option<UserId>,
        group: Option<UserId>,
    ) -> Result<(), AgentError>;

    async fn chmod(env_id: EnvironmentId, path: String, mode: u32) -> Result<(), AgentError>;

    async fn stat(env_id: EnvironmentId, path: String) -> Result<FileStat, AgentError>;

    // Metadata API
    async fn get_metadata(env_id: EnvironmentId, key: String)
        -> Result<Option<String>, AgentError>;

    async fn set_metadata(
        env_id: EnvironmentId,
        key: String,
        value: String,
    ) -> Result<(), AgentError>;
}
