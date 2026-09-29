# devmachine-skills

Agent Skills for operating Devmachine: `use-devmachine` (running, inspecting
and troubleshooting the CLI) and `create-devmachine-package` (writing a new
package).

- **Scope:** workspace
- **Category:** Coding agents
- **Needs:** none

## Settings

None.

## Credentials

None.

## Add it

```bash
devmachine packages add devmachine-skills --workspace acme
devmachine sync
devmachine skills add
```

`devmachine skills add` installs the skills onto your own computer, from the
pinned release; `devmachine skills list` shows what is installed and where.

## Notes

- This package only contributes the skills themselves
  (`skills/*/SKILL.md`); `devmachine skills` on your computer is what
  installs and links them for your agent tool.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [Agent skills](https://mydevmachine.sh/concepts/agent-skills/)
