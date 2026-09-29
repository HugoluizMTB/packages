# mac-mise

Installs mise's global tools from a list. For a `self: true` machine — your
own Mac.

- **Scope:** machine
- **Category:** macOS
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `bin` | `~/.local/bin/mise` | Where the mise binary is. |
| `tools` | `[]` | Tools to install globally, as `mise use -g` takes them, e.g. `node@lts`. |

## Credentials

None.

## Add it

```bash
devmachine machines add --self main
devmachine packages add mac-mise --machine main
devmachine sync
```

## Notes

- Expects mise already installed (for example by `mac-brew`); it does not
  install mise itself, only its global tools.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Your computer as a machine](https://mydevmachine.sh/how-it-works/your-computer-as-a-machine/)
