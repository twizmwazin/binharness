use std::io::{Seek, SeekFrom, Write};
use std::net::SocketAddr;
use std::sync::Arc;

use anyhow::Result;
use tarpc::context::Context;

use bh_agent_common::{
    AgentError, BhAgentService, EnvironmentId, FileId, FileOpenMode, FileOpenType, ProcessChannel,
    ProcessId, RemotePOpenConfig,
};
use bh_agent_common::{AgentError::*, UserId};

use crate::state::BhAgentState;
#[cfg(target_family = "unix")]
use crate::util::{chmod, chown, set_blocking, stat};
use crate::util::{read_generic, read_lines};

macro_rules! check_env_id {
    ($env_id:expr) => {
        if $env_id != 0 {
            return Err(AgentError::InvalidEnvironmentId);
        }
    };
}

#[derive(Clone)]
pub struct BhAgentServer {
    sockaddr: SocketAddr,
    state: Arc<BhAgentState>,
}

impl BhAgentServer {
    pub fn new(socket_addr: SocketAddr) -> Self {
        Self {
            sockaddr: socket_addr,
            state: Arc::new(BhAgentState::new()),
        }
    }
}

impl BhAgentService for BhAgentServer {
    async fn get_environments(self, _: Context) -> Vec<EnvironmentId> {
        // Our implementation currently only supports the default environment
        vec![0]
    }

    async fn get_tempdir(self, _: Context, env_id: EnvironmentId) -> Result<String, AgentError> {
        check_env_id!(env_id);

        Ok("/tmp".to_string()) // TODO: make configurable
    }

    async fn run_command(
        self,
        _: Context,
        env_id: EnvironmentId,
        config: RemotePOpenConfig,
    ) -> Result<ProcessId, AgentError> {
        check_env_id!(env_id);

        self.state.run_command(config)
    }

    async fn get_process_ids(
        self,
        _: Context,
        env_id: EnvironmentId,
    ) -> Result<Vec<ProcessId>, AgentError> {
        check_env_id!(env_id);

        self.state.get_process_ids()
    }

    async fn get_process_channel(
        self,
        _: Context,
        env_id: EnvironmentId,
        proc_id: ProcessId,
        channel: ProcessChannel,
    ) -> Result<FileId, AgentError> {
        check_env_id!(env_id);

        self.state.get_process_channel(&proc_id, channel)
    }

    async fn process_poll(
        self,
        _: Context,
        env_id: EnvironmentId,
        proc_id: ProcessId,
    ) -> Result<Option<u32>, AgentError> {
        check_env_id!(env_id);

        self.state.process_poll(&proc_id)
    }

    async fn process_wait(
        self,
        _: Context,
        env_id: EnvironmentId,
        proc_id: ProcessId,
        timeout: Option<u32>,
    ) -> Result<bool, AgentError> {
        check_env_id!(env_id);

        self.state.process_wait(&proc_id, timeout)
    }

    async fn process_returncode(
        self,
        _: Context,
        env_id: EnvironmentId,
        proc_id: ProcessId,
    ) -> Result<Option<u32>, AgentError> {
        check_env_id!(env_id);

        self.state.process_exit_code(&proc_id)
    }

    async fn file_open(
        self,
        _: Context,
        env_id: EnvironmentId,
        path: String,
        mode: FileOpenMode,
        type_: FileOpenType,
    ) -> Result<FileId, AgentError> {
        check_env_id!(env_id);

        self.state.open_path(path, mode, type_)
    }

    async fn file_close(
        self,
        _: Context,
        env_id: EnvironmentId,
        fd: FileId,
    ) -> Result<(), AgentError> {
        check_env_id!(env_id);

        self.state.close_file(&fd)
    }

    async fn file_is_closed(
        self,
        _: Context,
        env_id: EnvironmentId,
        fd: FileId,
    ) -> Result<bool, AgentError> {
        check_env_id!(env_id);

        self.state.is_file_closed(&fd)
    }

    async fn file_is_readable(
        self,
        _: Context,
        env_id: EnvironmentId,
        fd: FileId,
    ) -> Result<bool, AgentError> {
        check_env_id!(env_id);

        self.state
            .file_has_any_mode(&fd, &vec![FileOpenMode::Read, FileOpenMode::Update])
    }

    async fn file_read(
        self,
        _: Context,
        env_id: EnvironmentId,
        fd: FileId,
        num_bytes: Option<u32>,
    ) -> Result<Vec<u8>, AgentError> {
        check_env_id!(env_id);

        self.state
            .do_mut_operation(&fd, |file| {
                read_generic(file, num_bytes, self.state.file_type(&fd)?)
            })
            .and_then(|v| v.map_err(|e| IoError(e.to_string())))
    }

    async fn file_read_lines(
        self,
        _: Context,
        env_id: EnvironmentId,
        fd: FileId,
        hint: u32,
    ) -> Result<Vec<Vec<u8>>, AgentError> {
        check_env_id!(env_id);

        // TODO: support hint

        self.state
            .do_mut_operation(&fd, |file| {
                read_lines(file).map_err(|e| IoError(e.to_string()))
            })
            .and_then(|r| r)
    }

    async fn file_is_seekable(
        self,
        _: Context,
        env_id: EnvironmentId,
        fd: FileId,
    ) -> Result<bool, AgentError> {
        check_env_id!(env_id);

        todo!()
    }

    async fn file_seek(
        self,
        _: Context,
        env_id: EnvironmentId,
        fd: FileId,
        offset: i32,
        whence: i32,
    ) -> Result<(), AgentError> {
        check_env_id!(env_id);

        let from = match whence {
            0 => SeekFrom::Start(offset as u64),
            1 => SeekFrom::Current(offset as i64),
            2 => SeekFrom::End(offset as i64),
            _ => return Err(AgentError::InvalidSeekWhence),
        };

        self.state
            .do_mut_operation(&fd, |file| file.seek(from))
            .map(|_| ())
    }

    async fn file_tell(
        self,
        _: Context,
        env_id: EnvironmentId,
        fd: FileId,
    ) -> Result<i32, AgentError> {
        check_env_id!(env_id);

        todo!()
    }

    async fn file_is_writable(
        self,
        _: Context,
        env_id: EnvironmentId,
        fd: FileId,
    ) -> Result<bool, AgentError> {
        check_env_id!(env_id);

        self.state.file_has_any_mode(
            &fd,
            &vec![
                FileOpenMode::Write,
                FileOpenMode::ExclusiveWrite,
                FileOpenMode::Update,
                FileOpenMode::Append,
            ],
        )
    }

    async fn file_write(
        self,
        _: Context,
        env_id: EnvironmentId,
        fd: FileId,
        data: Vec<u8>,
    ) -> Result<(), AgentError> {
        check_env_id!(env_id);

        self.state
            .do_mut_operation(&fd, |file| file.write(&data))
            .map(|_| ())
    }

    async fn file_set_blocking(
        self,
        _: Context,
        env_id: EnvironmentId,
        fd: FileId,
        blocking: bool,
    ) -> Result<(), AgentError> {
        check_env_id!(env_id);

        #[cfg(target_family = "unix")]
        return self
            .state
            .do_mut_operation(&fd, |file| set_blocking(file, blocking))
            .map(|_| ());

        #[cfg(not(target_family = "unix"))]
        return Err(AgentError::UnsupportedPlatform);
    }

    async fn chown(
        self,
        _: Context,
        env_id: EnvironmentId,
        path: String,
        user: Option<UserId>,
        group: Option<UserId>,
    ) -> Result<(), AgentError> {
        check_env_id!(env_id);

        #[cfg(target_family = "unix")]
        return chown(path, user, group);

        #[cfg(not(target_family = "unix"))]
        return Err(AgentError::UnsupportedPlatform);
    }

    async fn chmod(
        self,
        _: Context,
        env_id: EnvironmentId,
        path: String,
        mode: u32,
    ) -> Result<(), AgentError> {
        check_env_id!(env_id);

        #[cfg(target_family = "unix")]
        return chmod(path, mode);

        #[cfg(not(target_family = "unix"))]
        return Err(AgentError::UnsupportedPlatform);
    }

    async fn stat(
        self,
        _: Context,
        env_id: EnvironmentId,
        path: String,
    ) -> Result<bh_agent_common::FileStat, AgentError> {
        check_env_id!(env_id);

        #[cfg(target_family = "unix")]
        return stat(path);

        #[cfg(not(target_family = "unix"))]
        return Err(AgentError::UnsupportedPlatform);
    }

    async fn get_metadata(
        self,
        _: Context,
        env_id: EnvironmentId,
        key: String,
    ) -> Result<Option<String>, AgentError> {
        check_env_id!(env_id);

        self.state.get_metadata(&key)
    }

    async fn set_metadata(
        self,
        _: Context,
        env_id: EnvironmentId,
        key: String,
        value: String,
    ) -> Result<(), AgentError> {
        check_env_id!(env_id);

        self.state.set_metadata(&key, &value)
    }
}
