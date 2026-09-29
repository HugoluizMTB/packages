# ssh_hardening

Turns off password authentication for good. `devmachine setup` does this once,
at first contact, before Ansible exists; this package keeps it that way on
every `sync`.

- **Scope:** machine
- **Category:** Security
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `service` | `""` | What systemd calls sshd. Empty means the name this distribution family uses — `ssh` on Debian and Ubuntu, `sshd` elsewhere. |

## Credentials

None.

## Add it

```bash
devmachine packages add ssh_hardening --machine main
devmachine sync
```

`ssh_hardening` is usually pulled in through
[`essentials`](../essentials/README.md).

## Notes

- Only turns password login off; the key `setup` installed is proven to work
  first, so a `sync` never locks you out of a working key-based login.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [`setup`](https://mydevmachine.sh/reference/commands/#setup)
