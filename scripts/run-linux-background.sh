#!/usr/bin/env bash
# Run independently of the terminal, with errors retained in the user journal.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ $# -eq 0 ]]; then set -- clock; fi
session_env=()
for name in XDG_CONFIG_HOME DISPLAY WAYLAND_DISPLAY XAUTHORITY XDG_SESSION_TYPE XDG_CURRENT_DESKTOP DBUS_SESSION_BUS_ADDRESS FCU_CLOCK_LATITUDE FCU_CLOCK_LONGITUDE FCU_CLOCK_DESKTOP_SHORTCUT; do
    if [[ -v "$name" ]]; then session_env+=("--setenv=$name=${!name}"); fi
done
exec systemd-run --user --unit=fcu-clock --collect \
    --property=Restart=on-failure --property=RestartSec=3 \
    "${session_env[@]}" -- "$project_dir/run-linux.sh" "$@"
