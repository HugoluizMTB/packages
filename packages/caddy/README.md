# caddy

A reverse proxy that gets its own certificates, and a one-page site that
answers 200 to prove the machine is reachable. Every other site is a file
another package drops into `/etc/caddy/sites.d` — `caddy` serves nothing else
by itself.

- **Scope:** machine
- **Category:** Web
- **Needs:** `firewall`

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `email` | `""` | The address the certificate authority writes to about an expiring certificate. Empty means an anonymous account. |
| `local_certs` | `false` | Sign certificates locally instead of asking Let's Encrypt. For a machine no name resolves to — a test VM, a private network — where the ACME challenge can never succeed. |
| `site` | `true` | Serve a one-page site straight from Caddy, no container behind it. It answers 200, proving the name, the certificate and the proxy in one request. |
| `site_domain` | `""` | The name the one-page site answers to, with its own certificate. Empty serves it on port 80 at the machine's address, over plain HTTP. It creates no DNS record — pointing the name is `devmachine dns add`. |

## Credentials

None.

## Add it

```bash
devmachine packages add caddy --machine main
devmachine sync
```

`caddy` is usually pulled in through [`essentials`](../essentials/README.md).

## Extension point

`caddy` declares `sites.d: /etc/caddy/sites.d`. Another package contributes a
site by extending it:

```yaml
extends:
  caddy.sites.d: files/my-site.caddy
```

`devmachine expose add` writes one of these files for a workspace's port; see
`devmachine expose list` to check what is live.

## Notes

- `site_domain` never creates a DNS record by itself; point the name at the
  machine with `devmachine dns add` (or `devmachine expose add`, which does
  both).

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Publishing a site](https://mydevmachine.sh/concepts/publishing/)
- [DNS](https://mydevmachine.sh/concepts/dns/)
