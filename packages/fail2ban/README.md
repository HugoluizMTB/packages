# fail2ban

fail2ban, with a jail for sshd.

- **Scope:** machine
- **Category:** Security
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `maxretry` | `5` | How many failures from one address before it is banned. |
| `bantime` | `3600` | How long a ban lasts, in seconds. |
| `ignoreip` | `"127.0.0.1/8 ::1"` | The addresses that are never banned, space separated. Loopback only by default — a wider range exempts everyone who shares it. |

## Credentials

None.

## Add it

```bash
devmachine packages add fail2ban --machine main
devmachine sync
```

## Notes

- Not part of [`essentials`](../essentials/README.md); add it explicitly when
  you want it.
- Widening `ignoreip` exempts everyone on that range, not just you — keep it
  narrow.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
