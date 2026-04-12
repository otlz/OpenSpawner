#!/bin/bash
# PlatformIO extension bootstrap for code-server.
# Starts as root to fix volume permissions, then drops to coder.
# PlatformIO penv is pre-installed at image build time and copied to the
# volume on first mount. The background fallback only runs if the penv
# was deleted from an existing volume.

if [ "$(id -u)" = "0" ]; then
    chown -R coder:coder /home/coder/.platformio /home/coder/project 2>/dev/null
    exec runuser -u coder -- "$0" "$@"
fi

# --- Running as coder ---

# Portable Python symlink (fast, non-blocking)
if [ ! -f "$HOME/.platformio/python3/bin/python3" ]; then
    mkdir -p "$HOME/.platformio/python3/bin"
    ln -sf /usr/bin/python3 "$HOME/.platformio/python3/bin/python3"
fi
mkdir -p "$HOME/.platformio/.cache/tmp"

# If penv is missing (volume was cleared), install in BACKGROUND
# so code-server starts immediately and the user sees the IDE.
if [ ! -f "$HOME/.platformio/penv/bin/platformio" ]; then
    (
        echo "[VCODER] PlatformIO Core missing, installing in background..."
        python3 -m venv "$HOME/.platformio/penv"
        "$HOME/.platformio/penv/bin/pip" install -U platformio 2>&1 | tail -1
        "$HOME/.platformio/penv/bin/python" -c "
import json, platform, time
with open('$HOME/.platformio/penv/state.json', 'w') as f:
    json.dump({
        'created_on': int(time.time()),
        'python': {'path': '$HOME/.platformio/penv/bin/python', 'version': platform.python_version()},
        'installer_version': '1.2.2',
        'platform': {'platform': platform.platform(), 'release': platform.release()}
    }, f)
"
        echo "[VCODER] PlatformIO Core installed (reload window to activate)"
    ) &
fi

export PATH="/home/coder/.platformio/penv/bin:/usr/local/bin:/usr/bin:$PATH"
exec code-server --bind-addr 0.0.0.0:8080 --auth none --ignore-last-opened /home/coder/project
