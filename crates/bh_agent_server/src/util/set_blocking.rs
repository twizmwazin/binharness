use nix::libc::{fcntl, F_GETFL, F_SETFL, O_NONBLOCK};
use std::io;
use std::os::unix::io::AsRawFd;

// TODO: This is using libc directly, but nix has a wrapper for this. We should use that instead.
pub fn set_blocking<T: AsRawFd>(fd: &T, blocking: bool) -> io::Result<()> {
    let raw_fd = fd.as_raw_fd();
    let flags = unsafe { fcntl(raw_fd, F_GETFL, 0) };
    if flags < 0 {
        return Err(io::Error::last_os_error());
    }

    let flags = if blocking {
        flags & !O_NONBLOCK
    } else {
        flags | O_NONBLOCK
    };
    let res = unsafe { fcntl(raw_fd, F_SETFL, flags) };
    if res != 0 {
        return Err(io::Error::last_os_error());
    }

    Ok(())
}
