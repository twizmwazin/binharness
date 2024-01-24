class BhAgentClient:
    @staticmethod
    def initialize_client(ip_addr: str, port: int) -> BhAgentClient: ...
    def get_environments(self) -> list[int]: ...
    def get_tempdir(self, env_id: int) -> str: ...
    def run_process(
        self,
        env_id: int,
        argv: list[str],
        stdin: bool,
        stdout: bool,
        stderr: bool,
        executable: str | None,
        env: list[tuple[str, str]] | None,
        cwd: str | None,
        setuid: int | None,
        setgid: int | None,
        setpgid: int | None,
    ) -> int: ...
    def get_process_channel(self, env_id: int, proc_id: int, channel: int) -> int: ...
    def process_poll(self, env_id: int, proc_id: int) -> int | None: ...
    def process_wait(self, env_id: int, proc_id: int, timeout: float | None) -> int: ...
    def process_returncode(self, env_id: int, proc_id: int) -> int | None: ...
    def file_open(self, env_id: int, path: str, mode_and_type: str) -> int: ...
    def file_close(self, env_id: int, fd: int) -> None: ...
    def file_is_closed(self, env_id: int, fd: int) -> bool: ...
    def file_is_readable(self, env_id: int, fd: int) -> bool: ...
    def file_read(self, env_id: int, fd: int, size: int | None) -> bytes: ...
    def file_read_lines(self, env_id: int, fd: int, hint: int) -> list[bytes]: ...
    def file_is_seekable(self, env_id: int, fd: int) -> bool: ...
    def file_seek(self, env_id: int, fd: int, offset: int, whence: int) -> int: ...
    def file_tell(self, env_id: int, fd: int) -> int: ...
    def file_is_writable(self, env_id: int, fd: int) -> bool: ...
    def file_write(self, env_id: int, fd: int, data: bytes) -> int: ...
    def chown(self, env_id: int, path: str, user: str, group: str) -> None: ...
    def chmod(self, env_id: int, path: str, mode: int) -> None: ...
