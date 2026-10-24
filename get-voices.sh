#!/bin/bash
##########################################################
##                       Clockoo                        ##
##      Optional download of piper and free voices      ##
##                   written in Bash                    ##
##                          🌞                          ##
##       by FranzBias 2026 · github.com/FranzBias       ##
##            Licensed under the MIT License            ##
##          See LICENSE file for full license.          ##
##########################################################
# SPDX-License-Identifier: MIT
# get-voices.sh — optional download of piper and Clockoo's 8 free voices.
#
# Why this file exists: Clockoo speaks with piper (fast, natural, offline),
# but piper and its voices are big (~500 MB) and come from other projects,
# so they are never bundled and never downloaded behind the user's back.
# The user runs this script on purpose; it asks before downloading,
# checks every file against a known SHA-256, and only installs voices
# whose licence allows free reuse (CC0, public domain, M-AILABS).
# Without it, Clockoo still speaks through spd-say.
#
# Usage: ./get-voices.sh [target_dir]
#   target_dir: default ~/.local/share/Clockoo/piper (Clockoo's default)
#
# by Franz & Aldus

set -euo pipefail

TARGET="${1:-$HOME/.local/share/Clockoo/piper}"
PIPER_VERSION="2023.11.14-2"
PIPER_URL="https://github.com/rhasspy/piper/releases/download/$PIPER_VERSION"
VOICES_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main"

# piper release archives (MIT licence), checked on 2026-10-23
declare -A PIPER_SHA=(
    [x86_64]=a50cb45f355b7af1f6d758c1b360717877ba0a398cc8cbe6d2a7a3a26e225992
    [aarch64]=fea0fd2d87c54dbc7078d0f878289f404bd4d6eea6e7444a77835d1537ab88eb
    [armv7l]=c6946fcd57c705ed1d4666ea880f80ba0bbbd14de62ecbdd13460baf3bac8e37
)

# voice path on Hugging Face | licence of its dataset | SHA-256 of .onnx,
# .onnx.json and MODEL_CARD
VOICES=(
    "it/it_IT/paola/medium/it_IT-paola-medium|CC0|6fc918b5a0ea6137382833dddfa567bffbe6a5060c02043c87192ee59c04210c|aea19c0a7fce29fbc359b93f10e7902854401e4c95ae2ea328ae516b15d296cf|c53fd0070dc93b438edbce06728eb83759ba030fff0cce523209ee4a0a6363c0"
    "it/it_IT/riccardo/x_low/it_IT-riccardo-x_low|M-AILABS (BSD-style)|1368de15f123275a7ef951c9e5e30be0f58a032daa14a0da44037443c1d1d21b|146ab9c634afe524e9fb7530f2510df7a42fb1db56b52658ca1fb3d98001a62a|7ce3b2fc4f454c84936887971574e436cc2154049b427a530f70bee050b2fdc6"
    "de/de_DE/kerstin/low/de_DE-kerstin-low|CC0|d352a7641892cebf2903859af94e9ba81a141110215fe3943bcda7f7da401b7a|56e708556b7b9b7a53c4f8957e021421e69f11a600962bba554cffbe72cf2d47|7019006374a5fe5358186d5f3333e9f904385e7bdfbb68bc85dafce1a3cddae5"
    "de/de_DE/thorsten/medium/de_DE-thorsten-medium|CC0|7e64762d8e5118bb578f2eea6207e1a35a8e0c30595010b666f983fc87bb7819|974adee790533adb273a1ac88f49027d2a1b8f0f2cf4905954a4791e79264e85|5196b5ab0794e6056263a1f37c18bec407b61ac187529bee29d1c366871e5c9e"
    "en/en_US/kristin/medium/en_US-kristin-medium|public domain|5849957f929cbf720c258f8458692d6103fff2f0e3d3b19c8259474bb06a18d4|5681426d4aead22195de70531eeeeddb46493cfaffc5764b2ea3db73428b651c|8c181b1d5f7d8152b914faab941fcbe6b8f0495e63e5189d6f27b8c68c8393fc"
    "en/en_US/ljspeech/medium/en_US-ljspeech-medium|public domain|6f52a751e2349abe7a76735eb09dc1875298c77ea2342ffd2fef79ff81b87f22|141d612cc0a95ed7efc1ca936b845c2364967f2e9217c5dbfcf69fc4d6c65860|fbee1529c89d36b3fe76d7e9f3f832dce17f44900a52d76a9bda735654766b4d"
    "en/en_US/norman/medium/en_US-norman-medium|public domain|b9739443232a80a59c7d18810dd856899bf16a7964725f5ab81ea49b1351cb71|6c2db7f558a4a8deb9fe822583c1c5105f6c4e834dd0f9de8ad17a888ee9fe1d|60eaf4d10009d1bd4a1aa555d337dae00f60421d72fee415b9139a021e7cb5d0"
    "en/en_US/john/medium/en_US-john-medium|public domain|789c6c875726e627ddee93d51d8727859abe9c091c3d141591f4b83c2072e988|af60f177b6b550f3d7a302720c0fb89e7f94a82b5dca464775ef63b1c69ba09a|a056da65cd70dcbda96fc3420fe8d3442dbf3c8b75f49cdf800a715b42e299d1"
)

for tool in curl sha256sum tar; do
    command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
done

ARCH="$(uname -m)"
if [ -z "${PIPER_SHA[$ARCH]:-}" ]; then
    echo "piper $PIPER_VERSION has no build for '$ARCH'." >&2
    exit 1
fi

cat <<EOF
Clockoo — optional voices

This downloads about 500 MB:
  • piper $PIPER_VERSION ($ARCH, MIT)   from github.com/rhasspy/piper
  • 8 voices (IT paola, riccardo · DE kerstin, thorsten ·
    EN kristin, ljspeech, norman, john)   from huggingface.co/rhasspy/piper-voices
into: $TARGET

Every file is checked against a known SHA-256 before it is kept.
EOF
read -r -p "Continue? [y/N] " answer
case "$answer" in [yYsSjJ]*) ;; *) echo "Nothing downloaded."; exit 0 ;; esac

mkdir -p "$TARGET/voices"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# fetch URL DEST SHA256 — skips a file that is already there and correct
fetch() {
    local url="$1" dest="$2" sha="$3"
    if [ -f "$dest" ] && echo "$sha  $dest" | sha256sum -c --status; then
        echo "  ok (already there)  $(basename "$dest")"
        return
    fi
    curl -fL --progress-bar -o "$TMP/part" "$url"
    if ! echo "$sha  $TMP/part" | sha256sum -c --status; then
        echo "  CHECKSUM MISMATCH: $url — file discarded" >&2
        exit 1
    fi
    mv "$TMP/part" "$dest"
    echo "  ok  $(basename "$dest")"
}

echo "piper:"
if [ -x "$TARGET/piper/piper" ]; then
    echo "  ok (already there)  piper"
else
    fetch "$PIPER_URL/piper_linux_$ARCH.tar.gz" "$TMP/piper.tar.gz" "${PIPER_SHA[$ARCH]}"
    tar -xzf "$TMP/piper.tar.gz" -C "$TARGET"
fi

echo "voices:"
for entry in "${VOICES[@]}"; do
    IFS='|' read -r path licence sha_onnx sha_json sha_card <<<"$entry"
    name="$(basename "$path")"
    dir="$(dirname "$path")"
    echo " $name ($licence)"
    fetch "$VOICES_URL/$path.onnx" "$TARGET/voices/$name.onnx" "$sha_onnx"
    fetch "$VOICES_URL/$path.onnx.json" "$TARGET/voices/$name.onnx.json" "$sha_json"
    fetch "$VOICES_URL/$dir/MODEL_CARD" "$TARGET/voices/$name.MODEL_CARD" "$sha_card"
done

echo
echo "Done. Voices are in $TARGET/voices."
if [ "$TARGET" != "$HOME/.local/share/Clockoo/piper" ]; then
    echo "Non-default folder: set \"piper_dir\": \"$TARGET\" in ~/.config/Clockoo/config.json"
fi
