# Scheduler units

The principles are in `SKILL.md`; these are the three unit files, each running a nightly command after 02:00 UTC through a tool installed with `uv`.
Keep them in the repo under `deploy/` and give the README the install line shown with each.

## launchd (macOS)

`deploy/com.example.myapp.nightly.plist`, installed with `cp` into `~/Library/LaunchAgents/` and `launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.example.myapp.nightly.plist`; `launchctl bootout gui/$UID/com.example.myapp.nightly` removes it, `launchctl kickstart -k gui/$UID/com.example.myapp.nightly` runs it now.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.example.myapp.nightly</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/me/.local/bin/uv</string>
    <string>run</string>
    <string>--project</string>
    <string>/Users/me/Git/myapp</string>
    <string>--frozen</string>
    <string>myapp-cli</string>
    <string>nightly</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>3</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>EnvironmentVariables</key>
  <dict>
    <key>MYAPP_DATA_DIR</key>
    <string>/Users/me/Library/Application Support/myapp</string>
  </dict>
  <key>StandardErrorPath</key>
  <string>/Users/me/Library/Logs/myapp/nightly.log</string>
</dict>
</plist>
```

- `StartCalendarInterval` is local time, so `Hour` is 3 to stay past midnight UTC in British Summer Time; a missed interval runs once on wake.
- `StandardErrorPath` captures the log, so the job installs no file handler; launchd never rotates it, so add a `TimedRotatingFileHandler` instead once the file matters.
- Secrets come from the `.env` the settings read, not `EnvironmentVariables`.
- For a service, replace `StartCalendarInterval` with `<key>KeepAlive</key><true/>`.

## systemd (Linux)

A timer and a service of the same name in `~/.config/systemd/user/`, enabled with `systemctl --user enable --now myapp-nightly.timer`; `systemctl --user list-timers` shows the next firing and `journalctl --user -u myapp-nightly` the log.
Run `loginctl enable-linger` once, or the user manager stops with the last logout and the timer with it.

`deploy/myapp-nightly.timer`:

```ini
[Unit]
Description=Fetch yesterday's readings

[Timer]
OnCalendar=*-*-* 02:00:00 UTC
Persistent=true
RandomizedDelaySec=5m

[Install]
WantedBy=timers.target
```

`deploy/myapp-nightly.service`:

```ini
[Unit]
Description=Fetch yesterday's readings

[Service]
Type=oneshot
WorkingDirectory=/home/me/Git/myapp
EnvironmentFile=/home/me/.config/myapp/env
ExecStart=/home/me/.local/bin/uv run --project /home/me/Git/myapp --frozen myapp-cli nightly
```

- `OnCalendar` takes a zone suffix, so the hour is stated in UTC directly; `Persistent=true` runs a missed firing at the next boot.
- The journal captures standard error and rotates it, so no file handler.
- `EnvironmentFile` holds the secrets, outside the repo, mode `600`.
- For a service, drop `Type=oneshot`, add `Restart=on-failure` and `RestartSec=10`, and enable the `.service` rather than a timer.

## GitHub Actions (cloud)

`.github/workflows/nightly.yml`, run on the default branch only; `workflow_dispatch` lets you run it by hand after a miss.

```yaml
name: nightly
on:
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:
concurrency:
  group: nightly
jobs:
  nightly:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10
      - run: uv sync --locked --no-dev
      - run: uv run myapp-cli nightly
        env:
          MYAPP_TOKEN: ${{ secrets.MYAPP_TOKEN }}
```

- `cron` is UTC unless a `timezone` key is set; the shortest interval is five minutes, and firings slip under load, so nothing downstream should assume the minute.
- `concurrency` without `cancel-in-progress` queues an overlapping run instead of killing the one in flight, the same policy as the lock.
- The runner has no data directory of its own, so the store is MotherDuck or an artefact uploaded at the end (see `store-data`); a workflow that writes to a local path keeps nothing.
- Pin the action versions as the uv docs show (`@<sha> # vN`) once the workflow is stable; the tags above are the current majors.
