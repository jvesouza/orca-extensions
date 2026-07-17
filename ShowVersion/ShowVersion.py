"""Extension that announces Orca's version, revision, and session type."""

import os

from orca import keybindings, orca_platform
from orca.command import Command, KeyboardCommand
from orca.extension import Extension


class ShowVersion(Extension):
    """Announces Orca's version and revision, optionally copying it to the clipboard."""

    GROUP_LABEL = "jve-extension"
    DESCRIPTION = "Announces Orca's version and revision, optionally copying it to the clipboard."
    WEBSITE = "https://github.com/jvesouza/orca-extensions"

    def _get_commands(self) -> list[Command]:
        return [
            self._create_show_version_command(),
            self._create_copy_version_to_clipboard_command(),
        ]

    def show_version(self) -> bool:
        """Announces the current version of Orca."""

        self._display_version_to_user(copy_to_clipboard=False)
        return True

    def copy_version_to_clipboard(self) -> bool:
        """Announces the current version of Orca and copies it to the clipboard."""

        self._display_version_to_user(copy_to_clipboard=True)
        return True

    def _display_version_to_user(self, copy_to_clipboard: bool = False) -> None:
        msg = self._generate_version_message()
        self.controller.present_message_internal(msg)
        if copy_to_clipboard:
            self.controller.set_clipboard_text_internal(msg)

    def _generate_version_message(self) -> str:
        parts = [f"Orca version: {orca_platform.version}"]
        if orca_platform.revision:
            parts.append(f"Revision: {orca_platform.revision}")

        session_type = os.environ.get("XDG_SESSION_TYPE") or ""
        session_desktop = os.environ.get("XDG_SESSION_DESKTOP") or ""
        session = f"{session_type} {session_desktop}".strip()
        if session:
            parts.append(f"Session: {session}")

        return ". ".join(parts)

    def _create_show_version_command(self) -> KeyboardCommand:
        return KeyboardCommand(
            "show_version",
            self.show_version,
            self.GROUP_LABEL,
            "Announces the current version of Orca",
            desktop_keybinding=self._get_keybinding("v", ctrl=True),
            laptop_keybinding=self._get_keybinding("v", ctrl=True),
        )

    def _create_copy_version_to_clipboard_command(self) -> KeyboardCommand:
        return KeyboardCommand(
            "copy_version_to_clipboard",
            self.copy_version_to_clipboard,
            self.GROUP_LABEL,
            "Announces the current version of Orca and copies it to the clipboard",
            desktop_keybinding=self._get_keybinding("v", ctrl=True, shift=True),
            laptop_keybinding=self._get_keybinding("v", ctrl=True, shift=True),
        )

    def _get_keybinding(
        self,
        key: str,
        ctrl: bool = False,
        shift: bool = False,
        alt: bool = False,
        orca_shift: bool = False,
        orca_ctrl: bool = False,
    ) -> keybindings.KeyBinding:
        mask = keybindings.ORCA_MODIFIER_MASK
        if ctrl:
            mask |= keybindings.CTRL_MODIFIER_MASK
        if shift:
            mask |= keybindings.SHIFT_MODIFIER_MASK
        if alt:
            mask |= keybindings.ALT_MODIFIER_MASK
        if orca_shift:
            mask |= keybindings.ORCA_SHIFT_MODIFIER_MASK
        if orca_ctrl:
            mask |= keybindings.ORCA_CTRL_MODIFIER_MASK
        return keybindings.KeyBinding(key, mask)
