# base

The base tools a development machine needs, plus a shared tmux config and a
`resume` session picker. Most other packages need it first.

- **Scope:** machine
- **Category:** Foundation
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `timezone` | `""` | The machine's timezone, as tzdata spells it. Empty leaves whatever the machine came with. |
| `hostname` | `""` | The machine's hostname. Empty leaves the one it already has. |
| `upgrade` | `false` | Upgrade every package already installed. Off, because that is the owner's decision, not a side effect of installing base tools. |
| `swap` | `""` | Size of a swapfile at `/swapfile`, such as `8G`. Empty leaves the machine alone. |

## Credentials

None.

## Add it

```bash
devmachine packages add base --machine main
devmachine sync
```

`base` is usually pulled in through [`essentials`](../essentials/README.md)
rather than added on its own.

## Notes

- `upgrade` is off by default so a sync never upgrades packages nobody asked
  for.
- `swap` only creates the swapfile when a size is given; it never resizes or
  removes one that already exists.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Package reference](https://mydevmachine.sh/reference/package-format/)
