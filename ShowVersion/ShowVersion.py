"""Extension that announces Orca's version, revision, and session type."""

import os

import gi

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi  # noqa: E402

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from orca import keybindings  # noqa: E402
from orca.command import Command, KeyboardCommand  # noqa: E402
from orca.extension import Extension  # noqa: E402


class ShowVersion(Extension):
    """Announces, copies, or displays in a dialog Orca's current version."""

    GROUP_LABEL = "Show Version"
    DESCRIPTION = (
        "Announces Orca's version and revision, optionally copying it to the clipboard or "
        "displaying it in a dialog."
    )
    WEBSITE = "https://github.com/jvesouza/orca-extensions"
    VERSION = "1.0.0"

    def _get_commands(self) -> list[Command]:
        return [
            self._create_show_version_command(),
            self._create_copy_version_to_clipboard_command(),
            self._create_show_version_dialog_command(),
        ]

    def show_version(self) -> bool:
        """Announces the current version of Orca."""

        self._display_version_to_user(copy_to_clipboard=False)
        return True

    def copy_version_to_clipboard(self) -> bool:
        """Announces the current version of Orca and copies it to the clipboard."""

        self._display_version_to_user(copy_to_clipboard=True)
        return True

    def show_version_dialog(self) -> bool:
        """Displays the current version of Orca in a dialog."""

        dialog = Gtk.MessageDialog(
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=self._generate_version_message(),
        )
        dialog.set_title(self.GROUP_LABEL)
        dialog.run()
        dialog.destroy()
        return True

    def _display_version_to_user(self, copy_to_clipboard: bool = False) -> None:
        msg = self._generate_version_message()
        self.controller.present_message_internal(msg)
        if copy_to_clipboard:
            self.controller.set_clipboard_text_internal(msg)

    def _generate_version_message(self) -> str:
        parts = [f"Orca version: {self.controller.get_version_internal()}"]

        atspi_version = Atspi.get_version()  # pylint: disable=no-value-for-parameter
        parts.append(
            f"AT-SPI2 version: {atspi_version[0]}.{atspi_version[1]}.{atspi_version[2]}"
        )

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

    def _create_show_version_dialog_command(self) -> KeyboardCommand:
        return KeyboardCommand(
            "show_version_dialog",
            self.show_version_dialog,
            self.GROUP_LABEL,
            "Displays the current version of Orca in a dialog",
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
