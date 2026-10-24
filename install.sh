#!/bin/bash
##########################################################
##                       Clockoo                        ##
##            Installer for the current user            ##
##                   written in Bash                    ##
##                          🌞                          ##
##       by FranzBias 2026 · github.com/FranzBias       ##
##            Licensed under the MIT License            ##
##          See LICENSE file for full license.          ##
##########################################################
# SPDX-License-Identifier: MIT
# install.sh — installs Clockoo 🐦⏰ for the current user.
#
# Why this file exists: the sources live in a git checkout, but the copy in use
# must live outside it (default ~/.local/share/Clockoo/app). This copies the
# files, adds the menu launcher, the tray autostart and the icon, and
# creates the timers. No sudo needed.
#
# Usage: ./install.sh          (CLOCKOO_DIR=/some/dir ./install.sh to choose the folder)
#
# by Franz & Aldus

set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
APPS="$HOME/.local/share/applications"
# Install folder: $CLOCKOO_DIR, else where an earlier install already is
# (read from its launcher, so updates never move it), else the default.
EXISTING="$(sed -n 's|^Exec=/usr/bin/python3 \(.*\)/clockoo_gui.py$|\1|p' \
    "$APPS/clockoo.desktop" 2>/dev/null | head -n 1)"
DEST="${CLOCKOO_DIR:-${EXISTING:-$HOME/.local/share/Clockoo/app}}"
AUTOSTART="$HOME/.config/autostart"
ICONS="$HOME/.local/share/icons/hicolor/scalable/apps"

mkdir -p "$DEST" "$APPS" "$AUTOSTART" "$ICONS"
for f in clockoo_core.py clockoo_i18n.py clockoo_ring.py clockoo_gui.py clockoo.svg; do
    install -m 0644 "$SRC/$f" "$DEST/$f"
done
chmod 0755 "$DEST/clockoo_gui.py" "$DEST/clockoo_ring.py"
# The bundled CC0 sounds (default sounds folder) and their credits.
mkdir -p "$DEST/sounds"
install -m 0644 "$SRC"/sounds/*.ogg "$SRC/sounds/CREDITS.md" "$DEST/sounds/"
install -m 0644 "$SRC/clockoo.svg" "$ICONS/clockoo.svg"
gtk-update-icon-cache -q -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

cat > "$APPS/clockoo.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Clockoo
Comment=Hourly cuckoo and alarms with voice
Comment[it]=Cucù orario e sveglie con voce
Comment[de]=Stündlicher Kuckuck und Wecker mit Stimme
Exec=/usr/bin/python3 $DEST/clockoo_gui.py
Icon=clockoo
Terminal=false
Categories=Utility;Clock;
Keywords=alarm;cuckoo;clock;sveglia;cucù;wecker;
StartupWMClass=clockoo_gui.py
EOF

cat > "$AUTOSTART/clockoo.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Clockoo (tray)
Exec=/usr/bin/python3 $DEST/clockoo_gui.py --hidden
Icon=clockoo
Terminal=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=5
EOF

# First apply: creates ~/.config/Clockoo/config.json and the timers.
/usr/bin/python3 -c "import sys; sys.path.insert(0, '$DEST'); import clockoo_core as c; e = c.apply(c.load_config()); print('\n'.join(e) or 'timers ok')"

echo "Clockoo installed in $DEST"
