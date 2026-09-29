# docker

Docker Engine and the Compose plugin, from Docker's own repository.

- **Scope:** machine
- **Category:** Containers
- **Needs:** `base`

## Settings

None.

## Credentials

None.

## Add it

```bash
devmachine packages add docker --machine main
devmachine sync
```

## Notes

- Not part of [`essentials`](../essentials/README.md); add it explicitly when
  you want it.
- Docker itself is installed here, but nobody is put in the `docker` group by
  this package. That happens through
  [`workspace`](../workspace/README.md)'s `groups` setting, and joining that
  group is effectively root on the machine — add it only to a workspace that
  needs it.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
