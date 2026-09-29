# workspace

The Linux account a person works in: a home nobody else can read, a git
identity and `~/dev`. Almost every other workspace-scoped package needs this
one first.

- **Scope:** workspace
- **Category:** Foundation
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `home` | `/home/<the account>` | Where the account's home is. Debian and Ubuntu put it under `/home`; a machine whose `useradd` is configured otherwise says so here. |
| `admin_home` | `/root` | The home of the account the CLI provisions with. Whatever reaches that account over SSH is what reaches this workspace. |
| `groups` | `[]` | Extra Linux groups the account joins. The `docker` group is one of them, and it is effectively root, so nobody joins it by accident. |
| `shell` | `""` | The login shell. Empty means whatever `useradd` would pick; the package that installs a shell (such as `zsh`) is the one that sets it. |
| `git_name` | `""` | The name on this workspace's commits. |
| `git_email` | `""` | The address on this workspace's commits. |
| `sign_commits` | `true` | Sign every commit and rebase, once a package such as `git-key` sets up a key. |
| `known_hosts` | `["github.com"]` | The hosts whose SSH host key is trusted in advance, so the first clone does not stop to ask a question nobody is there to answer. |

## Credentials

None.

## Add it

```bash
devmachine workspaces new acme
devmachine sync
```

`workspaces new` adds `workspace` (and the rest of
`defaults.workspace`) automatically; there is usually no need to
`packages add` it by hand.

## Notes

- **The `docker` group is effectively root.** Add it to `groups` only for a
  workspace that genuinely needs it.
- `sign_commits` only takes effect once a key exists — pair it with
  [`git-key`](../git-key/README.md) or a key set up by hand.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Machines and workspaces](https://mydevmachine.sh/concepts/machines-and-workspaces/)
