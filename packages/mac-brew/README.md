# mac-brew

Installs Homebrew taps, formulae and casks from lists. Never removes
anything. For a `self: true` machine — your own Mac.

- **Scope:** machine
- **Category:** macOS
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `prefix` | `/opt/homebrew` | Where Homebrew lives. `/usr/local` on an Intel Mac. |
| `taps` | `[]` | Homebrew taps to add. |
| `formulae` | `[]` | Homebrew formulae to install. |
| `casks` | `[]` | Homebrew casks to install. |
| `trusted_casks` | `[]` | Casks to trust, as full names `<tap>/<cask>`. Recent Homebrew refuses to load a cask from an unofficial tap until it is trusted, per item on purpose rather than per tap. |
| `trusted_formulae` | `[]` | Formulae to trust, as full names `<tap>/<formula>`, for the same reason as `trusted_casks`. |

## Credentials

None.

## Add it

```bash
devmachine machines add --self main
devmachine packages add mac-brew --machine main
devmachine workspaces defaults --add mac-brew
devmachine sync
```

## Notes

- Only installs what you list; it never removes a formula or cask you took
  out of the list.
- A cask or formula from an unofficial tap needs its full name in
  `trusted_casks`/`trusted_formulae` before Homebrew will load it.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Your computer as a machine](https://mydevmachine.sh/how-it-works/your-computer-as-a-machine/)
