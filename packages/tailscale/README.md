# tailscale

Joins the machine to a tailnet, so it is reachable without a public address.

- **Scope:** machine
- **Category:** Network
- **Needs:** `base`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `exit_node` | `false` | Advertise this machine as an exit node. Off unless asked for. |

## Credentials

| Name | Kind | Scope | Shareable | How to provide it |
| --- | --- | --- | --- | --- |
| `tailscale` | manual | machine | no | `devmachine login tailscale` |

`tailscale`'s login runs `tailscale up` on the machine, as the admin account,
and stores state at `/var/lib/tailscale/tailscaled.state`. It is not
shareable — each machine joins the tailnet for itself.

## Add it

```bash
devmachine packages add tailscale --machine main
devmachine login tailscale
devmachine sync
```

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Reaching your server](https://mydevmachine.sh/concepts/reaching-your-server/)
