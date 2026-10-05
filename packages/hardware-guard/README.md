# hardware-guard

Watches the machine's temperatures and battery every minute, sends alerts and
a daily heartbeat to a push URL, and shuts the machine down when a limit
holds. Meant for hardware nobody is watching, like a computer left running at
home.

- **Scope:** machine
- **Platforms:** Linux and macOS
- **Category:** Monitoring
- **Needs:** none

## Settings

| Setting | Default | What it does |
| --- | --- | --- |
| `interval_seconds` | `60` | How often the guard reads the sensors. |
| `warn_celsius` | `80` | The hottest sensor at or above this sends an alert. |
| `shutdown_celsius` | `90` | The hottest sensor at or above this for `sustain_seconds` shuts the machine down. Linux only. |
| `battery_warn_celsius` | `45` | The battery at or above this sends an alert. |
| `battery_shutdown_celsius` | `55` | The battery at or above this for `sustain_seconds` shuts the machine down. |
| `sustain_seconds` | `120` | How long a shutdown limit has to hold, so one spike never powers a machine off. |
| `shutdown` | `true` | Power off when a limit holds. `false` only alerts. |
| `notify_url` | `""` | Where alerts are POSTed as plain text, for example `https://ntfy.sh/<topic>`. Empty logs only. |
| `heartbeat_hours` | `24` | Send a short status this often, so silence means the machine is off or unreachable. `0` turns it off. |
| `repeat_minutes` | `30` | How long the same alert waits before it is sent again. |
| `battery_charge_limit` | `0` | Keep the battery below this percentage, where the firmware exposes `charge_control_end_threshold`. `0` leaves it alone. |

## Credentials

None. `notify_url` is a setting, but treat it like a password: anybody who
knows an ntfy topic can read it and post to it.

## Add it

```bash
devmachine packages add hardware-guard --machine home
devmachine machines edit home --set hardware-guard.notify_url=https://ntfy.sh/<topic>
devmachine sync --machine home
```

Then check what it reads, and that a notification arrives:

```bash
devmachine run --machine home --package hardware-guard -- status
devmachine run --machine home --package hardware-guard -- notify-test
```

## What it reads

- **Linux:** every zone under `/sys/class/thermal`, every `temp*_input` under
  `/sys/class/hwmon`, and the first battery under `/sys/class/power_supply`.
  A reading outside 1–150 °C is a missing or broken sensor and is skipped.
  It runs as root from a systemd timer, because powering off and writing the
  charge limit are root's to do.
- **macOS:** the battery through `ioreg`, and the CPU speed limit macOS sets
  under thermal pressure through `pmset -g therm`. macOS gives an ordinary
  user no CPU temperature, so `shutdown_celsius` does not apply there: a
  speed limit alerts, and the battery limits shut down. It runs as a launch
  agent of the logged-in user and shuts down through System Events.

## Notes

- Not part of [`essentials`](../essentials/README.md). A server in a data
  centre is watched by its provider; this is for hardware you own.
- A machine powered off by the guard stays off until somebody turns it on.
  That is the point: it does not come back up into the same heat.
- The heartbeat is how you learn the machine itself died — a guard cannot
  report its own power cut.
- The alert body is plain text and the headers are ntfy's (`Title`,
  `Priority`, `Tags`), so any webhook that takes a text body works too.

## Learn more

- [Packages](https://mydevmachine.sh/packages/)
- [ntfy](https://ntfy.sh/)
