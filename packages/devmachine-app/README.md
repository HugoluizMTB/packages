# devmachine-app

What the Devmachine macOS app asks a machine for, reached through
`devmachine run --package devmachine-app`. Not meant to be run by hand.

- **Scope:** machine
- **Category:** macOS
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `github_hosts` | `[]` | GitHub Enterprise hosts the context panel resolves pull requests on, each as `{host, proxy}` with `proxy` optional. `github.com` always works; this adds more. |

## Credentials

None.

## Add it

```bash
devmachine packages add devmachine-app --machine main
devmachine sync
```

## Notes

- Its entrypoint (`bin/devmachine-app`) only accepts the `context` command,
  called by the macOS app itself — `devmachine run --package devmachine-app
  --workspace acme -- context`.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [`run`](https://mydevmachine.sh/reference/commands/#run)
