# Scheduler units

The principles are in `SKILL.md`; these are the two unit files for a machine you own, each running a nightly command after 02:00 UTC through a tool installed with `uv`.
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
    <string>--log-file</string>
    <string>/Users/me/Library/Application Support/myapp/logs/nightly.log</string>
    <string>--log-level</string>
    <string>info</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/Users/me/Git/myapp</string>
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
  <key>StandardOutPath</key>
  <string>/Users/me/Library/Application Support/myapp/logs/launchd.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/me/Library/Application Support/myapp/logs/launchd.log</string>
</dict>
</plist>
```

- `StartCalendarInterval` is local time, so `Hour` is 3 to stay past midnight UTC in British Summer Time; a missed interval runs once on wake.
- `StandardOutPath` and `StandardErrorPath` catch the summary row and anything that escapes before logging is configured; the job's own log is the `--log-file`, rotated by the handler, since launchd never rotates.
- `WorkingDirectory` is the repo, so a relative path resolves there; the settings find the `.env` by its absolute path, and secrets come from it, not from `EnvironmentVariables`.
- The two `/Users/me/...` paths are the ones the README tells a new machine to edit.
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
ExecStart=/home/me/.local/bin/uv run --project /home/me/Git/myapp --frozen myapp-cli nightly --log-file /home/me/.local/share/myapp/logs/nightly.log --log-level info
```

- `OnCalendar` takes a zone suffix, so the hour is stated in UTC directly; `Persistent=true` runs a missed firing at the next boot.
- The journal captures standard output and standard error and rotates them, as the backstop for anything that escapes before logging is configured; the `--log-file` stays the job's own record, rotated by its handler.
- `EnvironmentFile` holds the secrets, outside the repo, mode `600`.
- For a service, drop `Type=oneshot`, add `Restart=on-failure` and `RestartSec=10`, and enable the `.service` rather than a timer.

## The status unit

Once an alert is earned (`SKILL.md`, Report the outcome), copy the nightly unit as `com.example.myapp.status` or `myapp-status.timer` and `.service`, with `status --alert` in place of `nightly` and its log options, firing a few hours after the nightly so a night that never started is already stale.

## GitHub Actions (cloud)

The `schedule` workflow runs where `deploy-project` decides, so its file and notes live in that skill's `references/github-actions.md`; what Actions does with a missed run is in `SKILL.md`, Schedule it.
