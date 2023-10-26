BinHarness
===

BinHarness is a framework to facilitate analyzing binary programs in various environments.

## Project layout
```
binharness
| crates: Main directory for rust code
  | bh_agent_client: Client code for communicating with the binharness agent
  | bh_agent_common: Shared code between the agent client and server
  | bh_agent_server: The agent server program
| python: Main directory for python code
  | binharness: Main python module
  | tests: Test code
```
