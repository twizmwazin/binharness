use anyhow::Result;
use bh_agent_common::{AgentError, FileStat, UserId};
use nix::sys::stat::stat as nix_stat;
use nix::unistd::{chown as nix_chown, Gid, Group, Uid, User};
use std::os::unix::fs::PermissionsExt;
use std::path::Path;

fn get_user_id(name: UserId) -> Result<Uid, AgentError> {
    match name {
        UserId::Id(id) => Ok(Uid::from_raw(id)),
        UserId::Name(name) => Ok(User::from_name(&name)?
            .ok_or(AgentError::UserNotFound(name))?
            .uid),
    }
}

fn get_group_id(name: UserId) -> Result<Gid, AgentError> {
    match name {
        UserId::Id(id) => Ok(Gid::from_raw(id)),
        UserId::Name(name) => Ok(Group::from_name(&name)?
            .ok_or(AgentError::UserNotFound(name))?
            .gid),
    }
}

pub fn chown(path: String, user: Option<UserId>, group: Option<UserId>) -> Result<(), AgentError> {
    // Convert user and group names to their respective IDs
    let uid = user.map(|n| get_user_id(n)).transpose()?;
    let gid = group.map(|n| get_group_id(n)).transpose()?;

    // Perform the chown operation
    nix_chown(Path::new(&path), uid, gid).map_err(|e| AgentError::from(e))?;

    Ok(())
}

pub fn chmod(path: String, mode: u32) -> Result<(), AgentError> {
    std::fs::set_permissions(Path::new(&path), PermissionsExt::from_mode(mode))?;
    Ok(())
}

pub fn stat(path: String) -> Result<FileStat, AgentError> {
    nix_stat(Path::new(&path))
        .map(|s| s.into())
        .map_err(|e| e.into())
}
