Binharness
===

Binharness is a framework to facilitate analyzing binary programs in various
environments. It enables users to specify _targets_ and _environments_ to
analyze those targets in.


## Features
- [x] Run targets in a local environment
- [x] Run targets in a remote environment using Binharness agent
- [x] Allow clients to detach from the agent and reconnect later (ie. for
      long-running analyses and road-warrior scenarios)
- [x] Automatically bootstrap a remote environment over SSH
- [x] Automatically bootstrap a remote environment in Docker
- [ ] Automatically bootstrap a remote environment in Kubernetes


## Quickstart
Binharness is currently in a pre-alpha state. While it is possible to use it,
expect the API to change as new ideas are explored.

### Concepts
- **Environment**: A machine that can run targets. This can be a local machine
  or a remote machine. It could also be a virtual machine or a container. At its
  core, Binharness is not about managing environments, but bootstraping some
  environments like containers is planned for ease of use.

  There are two seperate implemenations of the environment: a local environment
  that is implemented in Python, and a remote environment that is implemented in
  Rust and uses a client/server archetecture.

- **Target**: A program to analyze. A target exists independently of an
  environment. A target can be loaded from an environment, or it can be loaded
  from a file and "injected" into an environment where it is used.

- **Injection**: An injection is how Binharness models adding files into an
  environment.

- **Executor**: An executor is a way to run a target. It is a wrapper around
  the target that provides a consistent interface for running the target. It
  also provides a way to collect results from the target. Examples of programs
  that can be used to create Binharness Executors are tracers, fuzzers,
  debuggers and translation layers.


## Development
### Project layout
Binharness contains a few different components, written in a mix of Python in
Rust. The Rust code contains three crates: a client, a server, and a shared
library. The server is intended to be a highly-portable binary that can be
statically compiled and run in as many environments as possible. The client is
a PyO3-based Python module that can be imported and used by Python code. The
shared library contains code that is shared between the client and server. The
Python code implements the primary user-facing API, and is intended to be used
as a library in applications that use Binharness. The PyO3 module is intended
to be a relievely low-overhead wrapper around the Rust code, and is not intended
to be used directly by users. By comparison, the Python code is intended to
implement a higher-level, "Pythonic" API that is easy and intuitive to use.

The directories looks like this:
```
binharness/
  crates/
    bh_agent_client/ - Client code for communicating with the binharness agent
    bh_agent_common/ - Shared code between the agent client and server
    bh_agent_server/ - The agent server program
  python/
    binharness/ - User facing-python module
    tests/ - Test code
```

## Prior art
- [archr](https://github.com/angr/archr) - A framework for "target-based"
  program analysis. It is similar to Binharness in that it can run targets in
  local and containerized environeents, however it defines a target as the
  binary and the system or container where it is run. Binharness seeks to
  improve on this by separating the target from the environment, allowing more
  flexibility, as well as allowing detaching from an analysis and retrieving
  results later.
- [angr](https://github.com/angr/angr) - A binary analysis framework. angr is
  an excellent python-based framework for binary analysis, and it has good
  support for modeling the environment that a binary is run in, including
  controlling behaviour at the function level using simprocedures and at the OS
  level using SimOS. Binharness looks to avoid modeling the environment and
  instead allow the user to use an existing environment, like a container. For
  use cases that benefit from a tool like angr, Binharness looks to be able to
  integrate with it.
- [docker](https://www.docker.com/) - A containerization platform. Docker is
  the go-to tool for containerization, and has popularized using container
  images to couple programs with configured environements. While it has been
  successfully used for program analysis through existing tools like archr, it
  is not desgined for this use case and requires other tools to make effective
  use of it. Binharness looks to leverage docker and its ecosystem to take
  advatage of its strengths like image management and runtime isolation.
- [SSH](https://en.wikipedia.org/wiki/Secure_Shell) SSH is the primary protocol
  for remote access and management of machines. Binharness uses SSH as one of
  the primary ways to bootrap remote environments. In a previous version,
  Binharness used SSH as the primary way to communicate with remote environments
  as well, but this has been replaced with a custom protocol due to limitations
  of SSH.
- [Ansible](https://www.ansible.com/) - A configuration management tool. Ansible
  is a popular tool for configuring remote machines, and could be used as an
  alternative to Binharness for bootstrapping remote environments. However, it
  lacks support for collecting results from remote machines in a convenient way.
  It also doesn't have an interface to integrate analyses, so the user would
  need to manually orchestrate the analysis.
