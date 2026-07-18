# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A personal collection of [Orca](https://gitlab.gnome.org/GNOME/orca) (the GNOME screen reader)
user extensions. Orca loads user extensions from `~/.local/share/orca/extensions/`; this is an
early/experimental Orca feature (extensions must be explicitly approved by hash before Orca
loads them — see "Approving Extensions" below).

Each extension is a single, self-contained `.py` file living in its own top-level directory
(`ShowVersion/ShowVersion.py`, `SynthSettingsRing/SynthSettingsRing.py`). There is no shared code
between extensions, no package manager, no build step, and no test suite — Orca itself is the
runtime, and it is not a dependency you install via pip (see below).

## Commands

There is no build, package.json, or test runner in this repo. The only tooling used is `ruff`
(lint) and `mypy` (type check), run directly against the extension files:

```sh
ruff check .
mypy ShowVersion/ShowVersion.py SynthSettingsRing/SynthSettingsRing.py
```

No `pyproject.toml`/`ruff.toml`/`mypy.ini` exists in this repo, so both run with their default
settings. `mypy` will report `import-untyped` errors for the `orca` package itself (it ships no
`py.typed` marker) — that is expected and not a real error in the extension code; judge findings
past that line.

There is no way to unit-test an extension in isolation: `orca.*` modules are only meaningful
inside a running Orca session. "Testing" a change means installing and approving the extension
into a real Orca session:

```sh
cp <Extension>/<Extension>.py ~/.local/share/orca/extensions/
orca --approve-extension <Extension>.py
orca --replace   # or start Orca if it isn't running
```

Re-approval (re-running `--approve-extension`) is required every time the extension file's
contents change, since approval is keyed to a SHA256 hash of the file.

## Extension architecture (Orca's user-extension API)

Every extension is a subclass of `orca.extension.Extension`. Understanding this base class's
contract is the key to reading or modifying anything in this repo:

- **Class attributes**: `GROUP_LABEL` (required — user-visible name, also used to group
  keybindings), `DESCRIPTION`, `WEBSITE`, and similar metadata are read from the class *without
  executing the extension*, so they must be simple string constants, not computed values.
- **`_get_commands(self) -> list[Command]`**: returns the extension's `KeyboardCommand` objects.
  Each command wires a name, a bound method, `GROUP_LABEL`, a description, and optional
  `desktop_keybinding`/`laptop_keybinding` (`orca.keybindings.KeyBinding` built from a key plus a
  modifier mask, e.g. `keybindings.ORCA_MODIFIER_MASK | keybindings.CTRL_MODIFIER_MASK`). Command
  methods take no arguments and return `True` when handled. If a requested keybinding conflicts
  with a built-in Orca command or another extension, Orca registers the command unbound rather
  than failing — don't assume a keybinding is always live.
- **`self.controller`**: the only supported way to talk to Orca at runtime. All methods on it end
  in `_internal` by convention (e.g. `present_message_internal`, `get_value_internal`,
  `set_value_internal`, `execute_command_internal`, `set_clipboard_text_internal`). Public
  non-`_internal` functions elsewhere in Orca's own codebase are not part of the extension API and
  can change without notice — never import or call into Orca internals directly from an
  extension. `get_value_internal`/`set_value_internal`/`execute_command_internal` take a Orca
  module name (e.g. `"SpeechManager"`) and a property/command name; see
  `SynthSettingsRing.py`'s `_RingStop` table for real examples of the module/property/command
  names in use (`Rate`, `CurrentVoice`, `IncreaseRate`, `CyclePunctuationLevel`, etc.).
- **`self.settings`**: per-extension persisted settings (stored under Orca's active profile in
  dconf), accessed with `get(key, default=...)` / `set(key, value)` / `reset(key)`. Always pass an
  explicit default to `get()`. There are no registered per-key defaults — an unset key returns
  whatever default the caller passes.
- **`get_preferences(self) -> list[ExtensionPreference]`**: optional override that declares
  settings shown in Orca's generated preferences dialog (`ExtensionPreference.boolean`, `.string`,
  `.integer`, `.floating`, `.enum`, `.path`, `.color`, `.string_list`, `.dictionary`, `.info`). The
  preference key must match the key used with `self.settings.get()`.
- **Hooks**: `on_shutdown()` (must return quickly — Orca waits at most ~0.5s for all extensions'
  shutdown hooks), `on_speech_output(output)` / `on_braille_output(output)` (observe/replace/consume
  output before Orca speaks/displays it — latency-sensitive, avoid blocking work), and modal input
  handling via `command_manager.get_manager().set_modal_handler(self)` plus
  `will_handle_event`/`handle_event` (for temporarily observing or consuming keystrokes already
  bound to another Orca command — extensions must never grab the keyboard directly).

Both extensions in this repo follow the same shape: a small, private "table of stops/commands"
(a tuple of `NamedTuple`s in `SynthSettingsRing.py`, plain private methods in `ShowVersion.py`),
public command methods that call `self.controller.present_message_internal(...)` to speak
results, and `_get_keybinding()` helpers that build `keybindings.KeyBinding` instances from a key
plus modifier flags.

Orca's user-extensions docs list "stable convenience functions for creating non-preferences
user-extension UI" as still pending — there is no supported helper for showing an extension's
own window. Extensions aren't prevented from building one directly, though: `ShowVersion`'s
`show_version_dialog()` calls `gi.repository.Gtk` directly (`gi.require_version("Gtk", "3.0")`,
matching the GTK version Orca itself uses in-process) to pop up a `Gtk.MessageDialog`. Since Orca
already runs a GTK main loop in-process, this works without any extra threading, but the extension
owns that dialog's behavior and accessibility — Orca provides no support for it.

## Style conventions already in use

- Extension classes are documented with a one-line class docstring; command methods have a
  one-line docstring describing the user-facing effect, not the implementation.
- Private helpers are prefixed `_` and kept small (one responsibility each — e.g. splitting
  "move selection" from "adjust current value" from "announce a stop").
- Comments are rare and only used to explain *why* a non-obvious choice was made (see the two
  comments in `SynthSettingsRing.py` explaining why no stop is selected by default and why a
  disabled stop clears the selection instead of falling back to another stop).
