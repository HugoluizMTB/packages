---
name: use-devmachine
description: "Use when running, inspecting, or troubleshooting the Devmachine CLI itself — adding or editing a machine (including the local self:true machine) or workspace, adding a package to one, running sync, expose, tunnel, run --package, or any other devmachine subcommand, or diagnosing a devmachine error. Not for writing a new package's Ansible role (see create-devmachine-package)."
---

# Use Devmachine

Use the CLI as the source of truth. Do not replace a missing CLI operation with
ad-hoc SSH or an old Ansible repository without first identifying the missing
capability.

A **machine** is a server the CLI can reach, or the local computer itself when
marked `self: true` in `config.yml`. A **workspace** is a Linux account on a
machine (never on a self machine). Each machine or workspace lists the
**packages** it has — an Ansible role plus `package.yml`, the CLI's only unit
of persistent state. `sync` is what converges a machine to match the
configuration; most other configuration edits, including `expose` (which
writes a route under the workspace, not a live proxy), only take effect once
`sync` runs. `run --package <name>` invokes a package's declared entrypoint
directly, without going through `sync`.

## Start here

Always begin with these local, read-only commands:

```bash
devmachine config path
devmachine help --json
```

Then run `devmachine <command> --help` for the selected operation.

## Reference

Read the matching file under `references/` before guessing at behavior:

| Question | File |
| --- | --- |
| Exact flags, subcommands, or command behavior | `references/commands.md` |
| A configuration key or setting | `references/settings.md` |
| An error message | `references/troubleshooting.md` |
| Machines, workspaces, `self` | `references/concepts/machines-and-workspaces.md` |
| Configuration file layout | `references/concepts/configuration.md` |
| Packages | `references/concepts/packages.md` |
| DNS and public sites | `references/concepts/dns.md` and `references/concepts/publishing.md` |
| Credentials | `references/concepts/credentials.md` |
| Agent skills shipped by a package | `references/concepts/agent-skills.md` |

These are copies of the CLI's own docs, kept in sync by
`scripts/sync-skill-references.sh`. When a copy disagrees with the installed
binary, the binary wins: prefer `devmachine <command> --help` and `devmachine
packages schema` for the running binary's own truth.

## Safety boundary

- Configuration edits such as `packages add`, `workspaces edit`, and
  `workspaces defaults` are local until `sync`.
- Commands such as `doctor`, `run`, `stats`, `sync --check`, DNS, and `expose`
  may contact a configured machine.
- A machine appearing in `config.yml` is not permission to contact it. Obtain
  explicit approval for the exact command before touching a real machine.
- Use a disposable local machine for development and acceptance. Reuse one
  fake machine for related checks.
- Public writes require the command's explicit consent boundary; for example,
  unattended `expose add` uses `--publish`, not `--yes`.

## Persistent versus volatile state

Leave deliberately volatile software unmanaged. For state that must converge,
reuse a published package or create a local package; do not silently install it
with `run`. Use `run` to invoke a package entrypoint or for an explicitly
temporary operation.

## Before reporting completion

Run the command's dry-run mode when available, inspect the target named by the
effective configuration, apply only with the required approval, and verify the
result through a Devmachine command.
