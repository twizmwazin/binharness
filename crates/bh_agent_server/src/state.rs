use bimap::BiMap;
use log::{debug, trace};
use std::collections::HashMap;
use std::ffi::OsStr;
use std::fs::{File, OpenOptions};
use std::sync::{Arc, RwLock};
use std::thread::sleep;
use std::time::Duration;

use subprocess::{Popen, PopenConfig};

use bh_agent_common::AgentError::{
    InvalidFileDescriptor, InvalidProcessId, IoError, ProcessStartFailure, Unknown,
};
use bh_agent_common::{
    AgentError, FileId, FileOpenMode, FileOpenType, ProcessChannel, ProcessId, Redirection,
    RemotePOpenConfig,
};

// TODO: Someday a simple in-memory key value store might be a good idea
pub struct BhAgentState {
    files: RwLock<HashMap<FileId, Arc<RwLock<File>>>>,
    file_modes: RwLock<HashMap<FileId, FileOpenMode>>,
    file_types: RwLock<HashMap<FileId, FileOpenType>>,
    processes: RwLock<HashMap<ProcessId, Arc<RwLock<Popen>>>>,
    proc_stdin_ids: RwLock<BiMap<ProcessId, FileId>>,
    proc_stdout_ids: RwLock<BiMap<ProcessId, FileId>>,
    proc_stderr_ids: RwLock<BiMap<ProcessId, FileId>>,

    next_file_id: RwLock<FileId>,
    next_process_id: RwLock<ProcessId>,
}

impl BhAgentState {
    pub fn new() -> BhAgentState {
        Self {
            files: RwLock::new(HashMap::new()),
            file_modes: RwLock::new(HashMap::new()),
            file_types: RwLock::new(HashMap::new()),
            processes: RwLock::new(HashMap::new()),
            proc_stdin_ids: RwLock::new(BiMap::new()),
            proc_stdout_ids: RwLock::new(BiMap::new()),
            proc_stderr_ids: RwLock::new(BiMap::new()),

            next_file_id: RwLock::new(0),
            next_process_id: RwLock::new(0),
        }
    }

    fn take_file_id(&self) -> Result<FileId, AgentError> {
        let mut next_file_id = self.next_file_id.write()?;
        let file_id = *next_file_id;
        *next_file_id += 1;
        Ok(file_id)
    }

    fn take_proc_id(&self) -> Result<ProcessId, AgentError> {
        let mut next_process_id = self.next_process_id.write()?;
        let process_id = *next_process_id;
        *next_process_id += 1;
        Ok(process_id)
    }

    pub fn file_has_any_mode(
        &self,
        fd: &FileId,
        modes: &Vec<FileOpenMode>,
    ) -> Result<bool, AgentError> {
        trace!("Checking file {} for modes {:?}", fd, modes);
        Ok(modes.contains(
            self.file_modes
                .read()?
                .get(fd)
                .ok_or(InvalidFileDescriptor)?,
        ))
    }

    pub fn file_type(&self, fd: &FileId) -> Result<FileOpenType, AgentError> {
        trace!("Getting file type for {}", fd);
        self.file_types
            .read()?
            .get(fd)
            .ok_or(InvalidFileDescriptor)
            .map(|t| *t)
    }

    pub fn open_path(
        &self,
        path: String,
        mode: FileOpenMode,
        type_: FileOpenType,
    ) -> Result<FileId, AgentError> {
        let mut open_opts = OpenOptions::new();
        match mode {
            FileOpenMode::Read => open_opts.read(true),
            FileOpenMode::Write => open_opts.write(true).create(true),
            FileOpenMode::ExclusiveWrite => open_opts.write(true).create_new(true),
            FileOpenMode::Append => open_opts.append(true),
            FileOpenMode::Update => open_opts.read(true).write(true),
        };
        let file = open_opts.open(&path).map_err(|e| {
            eprintln!("Path: {}", path);
            eprintln!("Error opening file: {}", e);
            IoError
        })?;
        let file_id = self.take_file_id()?;
        self.files
            .write()?
            .insert(file_id, Arc::new(RwLock::new(file)));
        self.file_modes.write()?.insert(file_id, mode);
        self.file_types.write()?.insert(file_id, type_);
        Ok(file_id)
    }

    pub fn run_command(&self, config: RemotePOpenConfig) -> Result<ProcessId, AgentError> {
        let mut popenconfig = PopenConfig {
            stdin: match config.stdin {
                Redirection::None => subprocess::Redirection::None,
                Redirection::Save => subprocess::Redirection::Pipe,
            },
            stdout: match config.stdout {
                Redirection::None => subprocess::Redirection::None,
                Redirection::Save => subprocess::Redirection::Pipe,
            },
            stderr: match config.stderr {
                Redirection::None => subprocess::Redirection::None,
                Redirection::Save => subprocess::Redirection::Pipe,
            },
            detached: false,
            executable: config.executable.map(|s| s.into()),
            env: config.env.map(|v| {
                v.iter()
                    .map(|t| (t.0.clone().into(), t.1.clone().into()))
                    .collect()
            }),
            cwd: config.cwd.map(|s| s.into()),
            ..PopenConfig::default()
        };
        #[cfg(unix)]
        {
            popenconfig.setuid = config.setuid.or(popenconfig.setuid);
            popenconfig.setgid = config.setuid.or(popenconfig.setgid);
            popenconfig.setpgid = config.setpgid || popenconfig.setpgid;
        }

        let proc = Popen::create(
            config
                .argv
                .iter()
                .map(OsStr::new)
                .collect::<Vec<_>>()
                .as_slice(),
            popenconfig,
        )
        .map_err(|_| ProcessStartFailure)?;

        let proc_id = self.take_proc_id()?;

        // Stick the process channels into the file map
        if proc.stdin.is_some() {
            trace!("Saving stdin for process {}", proc_id);
            let file_id = self.take_file_id()?;
            self.proc_stdin_ids.write()?.insert(proc_id, file_id);
            self.file_modes
                .write()?
                .insert(file_id, FileOpenMode::Write);
            self.file_types
                .write()?
                .insert(file_id, FileOpenType::Binary);
        } else {
            trace!("Process {} has no stdin", proc_id);
        }
        if proc.stdout.is_some() {
            trace!("Saving stdout for process {}", proc_id);
            let file_id = self.take_file_id()?;
            self.proc_stdout_ids.write()?.insert(proc_id, file_id);
            self.file_modes.write()?.insert(file_id, FileOpenMode::Read);
            self.file_types
                .write()?
                .insert(file_id, FileOpenType::Binary);
        } else {
            trace!("Process {} has no stdout", proc_id);
        }
        if proc.stderr.is_some() {
            trace!("Saving stderr for process {}", proc_id);
            let file_id = self.take_file_id()?;
            self.proc_stdout_ids.write()?.insert(proc_id, file_id);
            self.file_modes.write()?.insert(file_id, FileOpenMode::Read);
            self.file_types
                .write()?
                .insert(file_id, FileOpenType::Binary);
        } else {
            trace!("Process {} has no stderr", proc_id);
        }

        // Move the proc to the process map
        self.processes
            .write()?
            .insert(proc_id, Arc::new(RwLock::new(proc)));

        Ok(proc_id)
    }

    pub fn get_process_channel(
        &self,
        proc_id: &ProcessId,
        channel: ProcessChannel,
    ) -> Result<FileId, AgentError> {
        let channel_ids = match channel {
            ProcessChannel::Stdin => &self.proc_stdin_ids,
            ProcessChannel::Stdout => &self.proc_stdout_ids,
            ProcessChannel::Stderr => &self.proc_stderr_ids,
        };

        channel_ids.read()?.get_by_left(proc_id).copied().ok_or({
            debug!("Failed to get process channel");
            debug!("Process ID: {}", proc_id);
            debug!("Channel: {:?}", channel);
            let proc_is_valid = self.processes.read().unwrap().contains_key(proc_id);
            debug!("Process is valid: {}", proc_is_valid);
            debug!(
                "Process with valid channels: {:?}",
                channel_ids.read().unwrap().left_values()
            );

            InvalidProcessId
        })
    }

    pub fn process_poll(&self, proc_id: &ProcessId) -> Result<Option<u32>, AgentError> {
        trace!("Polling process {}", proc_id);
        let proc = self
            .processes
            .read()?
            .get(proc_id)
            .ok_or(InvalidProcessId)?
            .clone();
        let exit_status = proc.write()?.poll();
        match exit_status {
            None => Ok(None),
            Some(status) => match status {
                subprocess::ExitStatus::Exited(code) => Ok(Some(code)),
                subprocess::ExitStatus::Signaled(code) => Ok(Some(code as u32)),
                subprocess::ExitStatus::Other(code) => Ok(Some(code as u32)),
                subprocess::ExitStatus::Undetermined => Err(Unknown),
            },
        }
    }

    pub fn process_wait(
        &self,
        proc_id: &ProcessId,
        timeout: Option<u32>,
    ) -> Result<bool, AgentError> {
        trace!("Waiting for process {}", proc_id);
        // This is implemented as a busy loop to avoid holding the write lock
        // for too long. Open to suggestions on how to improve this.
        let mut elapsed = Duration::from_millis(0);
        loop {
            match self.process_poll(proc_id)? {
                None => (),
                Some(_) => return Ok(false),
            }
            elapsed += Duration::from_millis(100);
            if elapsed < Duration::from_millis(timeout.unwrap_or(u32::MAX) as u64) {
                sleep(Duration::from_millis(100));
            } else {
                return Ok(true);
            }
        }
    }

    pub fn process_exit_code(&self, proc_id: &ProcessId) -> Result<Option<u32>, AgentError> {
        trace!("Getting exit code for process {}", proc_id);
        let proc = self
            .processes
            .read()?
            .get(proc_id)
            .ok_or(InvalidProcessId)?
            .clone();
        let exit_status = proc.read()?.exit_status();
        match exit_status {
            None => Ok(None),
            Some(status) => match status {
                subprocess::ExitStatus::Exited(code) => Ok(Some(code)),
                subprocess::ExitStatus::Signaled(code) => Ok(Some(code as u32)),
                subprocess::ExitStatus::Other(code) => Ok(Some(code as u32)),
                subprocess::ExitStatus::Undetermined => Err(Unknown),
            },
        }
    }

    pub fn close_file(&self, fd: &FileId) -> Result<(), AgentError> {
        trace!("Closing file {}", fd);
        drop(
            self.files
                .write()?
                .remove(fd)
                .ok_or(InvalidFileDescriptor)?,
        );
        Ok(())
    }

    pub fn is_file_closed(&self, fd: &FileId) -> Result<bool, AgentError> {
        Ok(self.files.read()?.contains_key(fd))
    }

    pub fn do_mut_operation<R: Sized>(
        &self,
        fd: &FileId,
        op: impl Fn(&mut File) -> R,
    ) -> Result<R, AgentError> {
        trace!("Doing mut operation on file {}", fd);

        // Get file logic
        if let Some(file_lock) = self.files.read()?.get(fd) {
            return Ok(op(&mut *file_lock.write()?));
        } else {
            trace!("File id map: {:?}", self.files.read()?);
        }

        // If these unwraps fail, the state is bad
        if let Some(pid) = self.proc_stdin_ids.read()?.get_by_right(fd) {
            let procs_binding = self.processes.read()?;
            let mut proc_binding = procs_binding.get(pid).unwrap().write()?;
            let file = proc_binding.stdin.as_mut().unwrap();
            return Ok(op(file));
        } else {
            trace!("Process stdin id map: {:?}", self.proc_stdin_ids.read()?);
        }
        if let Some(pid) = self.proc_stdout_ids.read()?.get_by_right(fd) {
            let procs_binding = self.processes.read()?;
            let mut proc_binding = procs_binding.get(pid).unwrap().write()?;
            let file = proc_binding.stdout.as_mut().unwrap();
            return Ok(op(file));
        } else {
            trace!("Process stdout id map: {:?}", self.proc_stdout_ids.read()?);
        }
        if let Some(pid) = self.proc_stderr_ids.read()?.get_by_right(fd) {
            let procs_binding = self.processes.read()?;
            let mut proc_binding = procs_binding.get(pid).unwrap().write()?;
            let file = proc_binding.stderr.as_mut().unwrap();
            return Ok(op(file));
        } else {
            trace!("Process stderr id map: {:?}", self.proc_stderr_ids.read()?);
        }

        Err(InvalidFileDescriptor)
    }
}
