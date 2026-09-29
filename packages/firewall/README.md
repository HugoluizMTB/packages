# firewall

ufw, with SSH open and HTTP optional. It needs the `community.general`
Ansible collection on the machine.

- **Scope:** machine
- **Category:** Security
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `http` | `true` | Open 80 and 443. A machine that hosts nothing can turn this off. |
| `mosh_interface` | `""` | The one interface mosh's UDP range is opened on. Empty means it is not opened at all, which keeps the range off a public edge. |
| `mosh_ports` | `"60000:61000"` | The UDP range mosh is given on that interface. |

## Credentials

None.

## Add it

```bash
devmachine packages add firewall --machine main
devmachine sync
```

`firewall` is usually pulled in through [`essentials`](../essentials/README.md).

## Notes

- **mosh is closed by default.** Set `firewall.mosh_interface` (for example
  `eth0`, or a tailnet interface such as `tailscale0`) to open the range; with
  no interface set, `devmachine mosh` cannot reach the machine at all.
- Requires the `community.general` collection on the machine
  (`ansible-galaxy collection install community.general`); `sync` fails with a
  clear message if it is missing.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Reaching your server](https://mydevmachine.sh/concepts/reaching-your-server/)
