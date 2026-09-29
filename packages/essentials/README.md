# essentials

What almost every machine wants, in one package: base tools, git, a firewall,
SSH with passwords kept off, and Caddy to publish sites with HTTPS. Docker is
not included — add it with [`docker`](../docker/README.md) when you want it.
It installs nothing itself; it only pulls in the packages it needs.

- **Scope:** machine
- **Category:** Foundation
- **Needs:** `base`, `git`, `firewall`, `ssh_hardening`, `caddy`

## Settings

None of its own; each package it needs keeps its own settings (see their
READMEs).

## Credentials

None of its own.

## Add it

`devmachine setup` adds `essentials` to a new machine automatically, so the
first `sync` installs it. Pass `--no-essentials` to start a machine with no
packages instead.

To add it to a machine that does not have it yet:

```bash
devmachine packages add essentials --machine main
devmachine sync
```

## Notes

- Pulls in [`firewall`](../firewall/README.md), whose mosh UDP range stays
  closed until `firewall.mosh_interface` is set.
- Pulls in [`ssh_hardening`](../ssh_hardening/README.md), which turns off
  password login on every sync, same as `devmachine setup` did once at first
  contact.
- Only a pinned package release that has `essentials` gets it through
  `setup`; an older pinned release starts the machine empty and says so.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [`setup`](https://mydevmachine.sh/reference/commands/#setup)
