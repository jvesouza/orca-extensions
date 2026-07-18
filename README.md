# orca-extensions

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Personal collection of [Orca](https://gitlab.gnome.org/GNOME/orca) (the GNOME screen reader)
user extensions.

Orca supports loading custom user extensions from `~/.local/share/orca/extensions/`. This is
an early/experimental Orca feature — extensions must be explicitly approved by the user before
Orca will load them, and Orca does not maintain an official extension store. See Orca's own
[user-extensions.md](https://gitlab.gnome.org/GNOME/orca/-/blob/main/docs/user-extensions.md)
for the full extension API, security model, and approval process.

## Extensions in this repository

### ShowVersion

Announces Orca's version, revision, AT-SPI2 version, and session type on demand, and can copy
that information to the clipboard or show it in a dialog.

Default keybindings:
- `Orca+Ctrl+V` — announce the current version
- `Orca+Ctrl+Shift+V` — announce the current version and copy it to the clipboard

The "Displays the current version of Orca in a dialog" command has no default keybinding; assign
one from Orca's Preferences window if you want one.

### SynthSettingsRing

An NVDA-style "synth settings ring": select a speech setting (rate, pitch, volume, voice,
synthesizer, voice set, punctuation level, capitalization style, indentation) and adjust it,
without opening any menu.

Default keybindings:
- `Orca+Right` / `Orca+Left` — select the next/previous ring setting
- `Orca+Up` / `Orca+Down` — increase/decrease the selected setting

Notes:
- Each setting in the ring can be individually enabled or disabled from the extension's own
  preferences page, in case you're not interested in adjusting some of them (open it from the
  User Extensions page in Orca's Preferences window).
- Values adjusted through the ring are **not saved** across an Orca restart — this matches
  Orca's own built-in rate/pitch/volume keys, which also only change the running session, not
  your saved Preferences.

## Installation

1. Copy the extension's `.py` file into `~/.local/share/orca/extensions/`. For example:
   ```sh
   cp SynthSettingsRing/SynthSettingsRing.py ~/.local/share/orca/extensions/
   ```
2. Approve the extension so Orca will load it:
   ```sh
   orca --approve-extension SynthSettingsRing.py
   ```
   (or use the User Extensions page in Orca's Preferences window)
3. Restart Orca (`orca --replace`), or start it if it isn't already running.

If you edit an already-approved extension, its hash changes and you'll need to re-approve it
the same way before Orca will load the new version.

## Feedback

Criticism, improvements, suggestions, and beers are all very welcome — feel free to open an
issue.

## Disclaimer

These are personal, unofficial extensions — not affiliated with or endorsed by the GNOME Orca
project. Provided as-is, with no warranty. User extensions can have broad access to your system
and accessibility data, so please review the code before installing.

## License

MIT — see [LICENSE](LICENSE).
