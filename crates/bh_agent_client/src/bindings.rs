use crate::client::build_client;
use anyhow::Result;
use bh_agent_common::{
    AgentError, BhAgentServiceClient, EnvironmentId, FileId, FileOpenMode, FileOpenType, FileStat,
    ProcessChannel, ProcessId, Redirection, RemotePOpenConfig, UserId,
};
use log::debug;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use pyo3::{pyclass, pymethods, pymodule, PyResult, Python};
use std::future::Future;
use std::net::{IpAddr, SocketAddr};
use std::str::FromStr;
use tarpc::client::RpcError;
use tarpc::context;
use tokio::runtime;

#[pyclass]
struct BhAgentClient {
    tokio_runtime: runtime::Runtime,
    client: BhAgentServiceClient,
}

fn run_in_runtime<F, R>(client: &BhAgentClient, fut: F) -> PyResult<R>
where
    F: Future<Output = Result<Result<R, AgentError>, RpcError>> + Sized,
{
    client
        .tokio_runtime
        .block_on(fut)
        .map_err(|e| PyRuntimeError::new_err(e.to_string()))
        .map(|r| r.map_err(|e| PyRuntimeError::new_err(e.to_string())))
        .and_then(|r| r)
}

#[pymethods]
impl BhAgentClient {
    #[staticmethod]
    fn initialize_client(ip_addr: String, port: u16) -> PyResult<Self> {
        debug!("Initializing client with {}:{}", ip_addr, port);

        let ip_addr = IpAddr::from_str(&ip_addr)?;
        let socket_addr = SocketAddr::new(ip_addr, port);

        let tokio_runtime = runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .unwrap();
        match tokio_runtime.block_on(build_client(socket_addr)) {
            Ok(client) => Ok(Self {
                tokio_runtime,
                client,
            }),
            Err(e) => Err(PyRuntimeError::new_err(format!(
                "Failed to initialize client: {}",
                e
            ))),
        }
    }

    fn get_environments(&self) -> PyResult<Vec<EnvironmentId>> {
        debug!("Getting environments");

        self.tokio_runtime
            .block_on(self.client.get_environments(context::current()))
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    fn get_tempdir(&self, env_id: EnvironmentId) -> PyResult<String> {
        debug!("Getting tempdir for environment {}", env_id);

        run_in_runtime(self, self.client.get_tempdir(context::current(), env_id))
    }

    fn run_process(
        &self,
        env_id: EnvironmentId,
        argv: Vec<String>,
        stdin: bool,
        stdout: bool,
        stderr: bool,
        executable: Option<String>,
        env: Option<Vec<(String, String)>>,
        cwd: Option<String>,
        setuid: Option<u32>,
        setgid: Option<u32>,
        setpgid: bool,
    ) -> PyResult<ProcessId> {
        debug!(
            "Running process with argv {:?}, stdin {}, stdout {}, stderr {}, executable {:?}, env {:?}, cwd {:?}, setuid {:?}, setgid {:?}, setpgid {}",
            argv,
            stdin,
            stdout,
            stderr,
            executable,
            env,
            cwd,
            setuid,
            setgid,
            setpgid,);

        let config = RemotePOpenConfig {
            argv,
            stdin: match stdin {
                true => Redirection::Save,
                false => Redirection::None,
            },
            stdout: match stdout {
                true => Redirection::Save,
                false => Redirection::None,
            },
            stderr: match stderr {
                true => Redirection::Save,
                false => Redirection::None,
            },
            executable,
            env,
            cwd,
            setuid,
            setgid,
            setpgid,
        };
        run_in_runtime(
            self,
            self.client.run_command(context::current(), env_id, config),
        )
    }

    fn get_process_channel(
        &self,
        env_id: EnvironmentId,
        proc_id: ProcessId,
        channel: i32, // TODO: This is just 0, 1, 2 for now
    ) -> PyResult<FileId> {
        debug!(
            "Getting process channel for environment {}, process {}, channel {}",
            env_id, proc_id, channel
        );

        run_in_runtime(
            self,
            self.client.get_process_channel(
                context::current(),
                env_id,
                proc_id,
                match channel {
                    0 => ProcessChannel::Stdin,
                    1 => ProcessChannel::Stdout,
                    2 => ProcessChannel::Stderr,
                    _ => return Err(PyRuntimeError::new_err("Invalid channel")),
                },
            ),
        )
    }

    fn process_poll(&self, env_id: EnvironmentId, proc_id: ProcessId) -> PyResult<Option<u32>> {
        debug!(
            "Polling process for environment {}, process {}",
            env_id, proc_id
        );

        run_in_runtime(
            self,
            self.client
                .process_poll(context::current(), env_id, proc_id),
        )
    }

    fn process_wait(
        &self,
        env_id: EnvironmentId,
        proc_id: ProcessId,
        timeout: Option<f64>,
    ) -> PyResult<bool> {
        debug!(
            "Waiting for process for environment {}, process {}, timeout {:?}",
            env_id, proc_id, timeout
        );

        run_in_runtime(
            self,
            self.client.process_wait(
                context::current(),
                env_id,
                proc_id,
                match timeout {
                    Some(t) => Some((t * 1000.0) as u32),
                    None => None,
                },
            ),
        )
    }

    fn process_returncode(
        &self,
        env_id: EnvironmentId,
        proc_id: ProcessId,
    ) -> PyResult<Option<u32>> {
        debug!(
            "Getting process returncode for environment {}, process {}",
            env_id, proc_id
        );

        run_in_runtime(
            self,
            self.client
                .process_returncode(context::current(), env_id, proc_id),
        )
    }

    // File IO
    fn file_open(
        &self,
        env_id: EnvironmentId,
        path: String,
        mode_and_type: String,
    ) -> PyResult<FileId> {
        debug!(
            "Opening file for environment {}, path {}, mode_and_type {}",
            env_id, path, mode_and_type
        );

        // Mode parsing
        let mut mode = FileOpenMode::Read;
        mode_and_type.chars().for_each(|c| match c {
            'r' => mode = FileOpenMode::Read,
            'w' => mode = FileOpenMode::Write,
            'x' => mode = FileOpenMode::ExclusiveWrite,
            'a' => mode = FileOpenMode::Append,
            '+' => mode = FileOpenMode::Update,
            _ => {}
        });

        // Type parsing
        let mut type_ = FileOpenType::Text;
        if mode_and_type.contains("b") {
            type_ = FileOpenType::Binary;
        }

        run_in_runtime(
            self,
            self.client
                .file_open(context::current(), env_id, path, mode, type_),
        )
    }

    fn file_close(&self, env_id: EnvironmentId, fd: FileId) -> PyResult<()> {
        debug!("Closing file for environment {}, fd {}", env_id, fd);

        run_in_runtime(self, self.client.file_close(context::current(), env_id, fd))
    }

    fn file_is_closed(&self, env_id: EnvironmentId, fd: FileId) -> PyResult<bool> {
        debug!(
            "Checking if file is closed for environment {}, fd {}",
            env_id, fd
        );

        run_in_runtime(
            self,
            self.client.file_is_closed(context::current(), env_id, fd),
        )
    }

    fn file_is_readable(&self, env_id: EnvironmentId, fd: FileId) -> PyResult<bool> {
        debug!(
            "Checking if file is readable for environment {}, fd {}",
            env_id, fd
        );

        run_in_runtime(
            self,
            self.client.file_is_readable(context::current(), env_id, fd),
        )
    }

    fn file_read(
        &self,
        py: Python,
        env_id: EnvironmentId,
        fd: FileId,
        num_bytes: Option<u32>,
    ) -> PyResult<Py<PyBytes>> {
        debug!(
            "Reading file for environment {}, fd {}, num_bytes {:?}",
            env_id, fd, num_bytes
        );

        run_in_runtime(
            self,
            self.client
                .file_read(context::current(), env_id, fd, num_bytes),
        )
        .map(|bytes| PyBytes::new(py, bytes.as_slice()).into())
    }

    fn file_read_lines(
        &self,
        py: Python,
        env_id: EnvironmentId,
        fd: FileId,
        hint: u32,
    ) -> PyResult<Vec<Py<PyBytes>>> {
        debug!(
            "Reading file lines for environment {}, fd {}, hint {}",
            env_id, fd, hint
        );

        run_in_runtime(
            self,
            self.client
                .file_read_lines(context::current(), env_id, fd, hint),
        )
        .map(|lines| {
            lines
                .into_iter()
                .map(|bytes| PyBytes::new(py, bytes.as_slice()).into())
                .collect()
        })
    }

    fn file_is_seekable(&self, env_id: EnvironmentId, fd: FileId) -> PyResult<bool> {
        debug!(
            "Checking if file is seekable for environment {}, fd {}",
            env_id, fd
        );

        run_in_runtime(
            self,
            self.client.file_is_seekable(context::current(), env_id, fd),
        )
    }

    fn file_seek(
        &self,
        env_id: EnvironmentId,
        fd: FileId,
        offset: i32,
        whence: i32,
    ) -> PyResult<()> {
        debug!(
            "Seeking file for environment {}, fd {}, offset {}, whence {}",
            env_id, fd, offset, whence
        );

        run_in_runtime(
            self,
            self.client
                .file_seek(context::current(), env_id, fd, offset, whence),
        )
    }

    fn file_tell(&self, env_id: EnvironmentId, fd: FileId) -> PyResult<i32> {
        debug!("Telling file for environment {}, fd {}", env_id, fd);

        run_in_runtime(self, self.client.file_tell(context::current(), env_id, fd))
    }

    fn file_is_writable(&self, env_id: EnvironmentId, fd: FileId) -> PyResult<bool> {
        debug!(
            "Checking if file is writable for environment {}, fd {}",
            env_id, fd
        );

        run_in_runtime(
            self,
            self.client.file_is_writable(context::current(), env_id, fd),
        )
    }

    fn file_write(&self, env_id: EnvironmentId, fd: FileId, data: Vec<u8>) -> PyResult<()> {
        debug!(
            "Writing file for environment {}, fd {}, data length {:?}",
            env_id,
            fd,
            data.len()
        );

        run_in_runtime(
            self,
            self.client.file_write(context::current(), env_id, fd, data),
        )
    }

    fn chown(
        &self,
        env_id: EnvironmentId,
        path: String,
        user: Option<String>,
        group: Option<String>,
    ) -> PyResult<()> {
        debug!(
            "Chowning file for environment {}, path {}, user {:?}, group {:?}",
            env_id, path, user, group
        );

        let parsed_user = user.map(|u| match u.parse::<u32>() {
            Ok(id) => UserId::Id(id),
            Err(_) => UserId::Name(u),
        });
        let parsed_group = group.map(|g| match g.parse::<u32>() {
            Ok(id) => UserId::Id(id),
            Err(_) => UserId::Name(g),
        });

        run_in_runtime(
            self,
            self.client
                .chown(context::current(), env_id, path, parsed_user, parsed_group),
        )
    }

    fn chmod(&self, env_id: EnvironmentId, path: String, mode: u32) -> PyResult<()> {
        debug!(
            "Chmoding file for environment {}, path {}, mode {}",
            env_id, path, mode
        );

        run_in_runtime(
            self,
            self.client.chmod(context::current(), env_id, path, mode),
        )
    }

    fn stat(&self, env_id: EnvironmentId, path: String) -> PyResult<FileStat> {
        debug!("Stating file for environment {}, path {}", env_id, path);

        run_in_runtime(self, self.client.stat(context::current(), env_id, path))
    }
}

#[pymodule]
pub fn bh_agent_client(_py: Python, m: &PyModule) -> PyResult<()> {
    pyo3_log::init();
    m.add_class::<FileStat>()?;
    m.add_class::<BhAgentClient>()?;
    Ok(())
}
