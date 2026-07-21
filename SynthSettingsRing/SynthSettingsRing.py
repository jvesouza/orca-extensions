"""Extension implementing an NVDA-style synth settings ring for Orca."""

from typing import NamedTuple, cast

from orca import keybindings
from orca.command import Command, KeyboardCommand
from orca.extension import Extension, ExtensionPreference


class _RingStop(NamedTuple):
    """One selectable stop on the settings ring."""

    key: str
    label: str
    kind: str  # "numeric", "list", "cycle", or "toggle"
    module: str = "SpeechManager"
    property: str = ""
    increase_command: str = ""
    decrease_command: str = ""
    available_property: str = ""
    values: tuple[str, ...] = ()
    toggle_command: str = ""


class SynthSettingsRing(Extension):
    """Lets you select a speech setting and adjust its value, like NVDA's synth settings ring."""

    GROUP_LABEL = "Synth Settings Ring"
    DESCRIPTION = (
        "Cycle through speech settings (rate, pitch, volume, voice, ...) and adjust the "
        "selected one, similar to NVDA's synth settings ring. Individual settings can be "
        "enabled or disabled from this extension's preferences."
    )
    WEBSITE = "https://github.com/jvesouza/orca-extensions"
    VERSION = "1.1.0"

    _PERSIST_KEY = "persist-values"
    _VALUES_KEY = "ring-values"

    _STOPS: tuple[_RingStop, ...] = (
        _RingStop(
            "rate",
            "Rate",
            "numeric",
            property="Rate",
            increase_command="IncreaseRate",
            decrease_command="DecreaseRate",
        ),
        _RingStop(
            "pitch",
            "Pitch",
            "numeric",
            property="Pitch",
            increase_command="IncreasePitch",
            decrease_command="DecreasePitch",
        ),
        _RingStop(
            "volume",
            "Volume",
            "numeric",
            property="Volume",
            increase_command="IncreaseVolume",
            decrease_command="DecreaseVolume",
        ),
        _RingStop(
            "pitch-range",
            "Pitch range",
            "numeric",
            property="PitchRange",
            increase_command="IncreasePitchRange",
            decrease_command="DecreasePitchRange",
        ),
        _RingStop(
            "voice",
            "Voice",
            "list",
            property="CurrentVoice",
            available_property="AvailableVoices",
        ),
        _RingStop(
            "synthesizer",
            "Synthesizer",
            "list",
            property="CurrentSynthesizer",
            available_property="AvailableSynthesizers",
        ),
        _RingStop(
            "voice-set",
            "Voice set",
            "list",
            property="ActiveVoiceSet",
            available_property="AvailableVoiceSets",
        ),
        _RingStop(
            "punctuation-level",
            "Punctuation level",
            "cycle",
            property="PunctuationLevel",
            values=("none", "some", "most", "all"),
        ),
        _RingStop(
            "capitalization-style",
            "Capitalization style",
            "cycle",
            property="CapitalizationStyle",
            values=("none", "spell", "icon"),
        ),
        _RingStop(
            "indentation",
            "Indentation",
            "toggle",
            module="SpeechPresenter",
            property="SpeakIndentation",
            toggle_command="ToggleIndentation",
        ),
    )

    def __init__(self) -> None:
        super().__init__()
        # No stop is selected until the user explicitly chooses one with next/previous,
        # so increase/decrease never act on a stop the user didn't pick.
        self._current_key: str | None = None
        self._list_selection: dict[str, str] = {}
        self._available_cache: dict[str, list[str]] = {}

    def on_ready(self) -> None:
        """Restores persisted ring values and pre-populates option caches on startup."""

        self._initialize_ring_state()

    def on_enabled(self) -> None:
        """Restores persisted ring values and pre-populates option caches when re-enabled.

        Toggling any extension in the preferences page reloads every user extension from
        scratch (see extension_loader.reload_user_extensions), so this instance never goes
        through on_ready() - it needs the same one-time setup on_enabled() gives it instead.
        """

        self._initialize_ring_state()

    def _initialize_ring_state(self) -> None:
        self._restore_persisted_values()
        for stop in self._STOPS:
            if stop.kind == "list":
                self._available_options(stop)

    def get_preferences(self) -> list[ExtensionPreference]:
        return [
            ExtensionPreference.boolean(
                self._PERSIST_KEY, "Remember ring values across Orca restarts", False
            ),
            *(
                ExtensionPreference.boolean(f"enable-{stop.key}", stop.label, True)
                for stop in self._STOPS
            ),
        ]

    def _get_commands(self) -> list[Command]:
        return [
            KeyboardCommand(
                "next_ring_setting",
                self.next_ring_setting,
                self.GROUP_LABEL,
                "Selects the next speech settings ring setting",
                desktop_keybinding=self._get_keybinding("Right"),
                laptop_keybinding=self._get_keybinding("Right"),
            ),
            KeyboardCommand(
                "previous_ring_setting",
                self.previous_ring_setting,
                self.GROUP_LABEL,
                "Selects the previous speech settings ring setting",
                desktop_keybinding=self._get_keybinding("Left"),
                laptop_keybinding=self._get_keybinding("Left"),
            ),
            KeyboardCommand(
                "increase_ring_value",
                self.increase_ring_value,
                self.GROUP_LABEL,
                "Increases the value of the selected speech settings ring setting",
                desktop_keybinding=self._get_keybinding("Up"),
                laptop_keybinding=self._get_keybinding("Up"),
            ),
            KeyboardCommand(
                "decrease_ring_value",
                self.decrease_ring_value,
                self.GROUP_LABEL,
                "Decreases the value of the selected speech settings ring setting",
                desktop_keybinding=self._get_keybinding("Down"),
                laptop_keybinding=self._get_keybinding("Down"),
            ),
        ]

    def next_ring_setting(self) -> bool:
        """Selects the next enabled stop on the settings ring."""

        return self._move_selection(1)

    def previous_ring_setting(self) -> bool:
        """Selects the previous enabled stop on the settings ring."""

        return self._move_selection(-1)

    def increase_ring_value(self) -> bool:
        """Increases the value of the currently selected stop."""

        return self._adjust_current_stop(1)

    def decrease_ring_value(self) -> bool:
        """Decreases the value of the currently selected stop."""

        return self._adjust_current_stop(-1)

    def _move_selection(self, direction: int) -> bool:
        stops = self._enabled_stops()
        if not stops:
            self.controller.present_message_internal(
                "No settings ring options are enabled."
            )
            return True

        index = self._index_of_current(stops)
        if index == -1:
            new_index = 0 if direction > 0 else len(stops) - 1
        else:
            new_index = (index + direction) % len(stops)
        stop = stops[new_index]
        self._current_key = stop.key
        self._announce_stop(stop)
        return True

    def _adjust_current_stop(self, direction: int) -> bool:
        if not self._enabled_stops():
            self.controller.present_message_internal(
                "No settings ring options are enabled."
            )
            return True

        stop = self._current_stop()
        if stop is None:
            self.controller.present_message_internal(
                "No settings ring option is selected. Use next or previous to choose one."
            )
            return True

        if stop.kind == "numeric":
            command = stop.increase_command if direction > 0 else stop.decrease_command
            self.controller.execute_command_internal(stop.module, command)
        elif stop.kind in ("list", "cycle"):
            self._cycle_stop(stop, direction)
        elif stop.kind == "toggle":
            self.controller.execute_command_internal(stop.module, stop.toggle_command)

        self._persist_current_value(stop)
        return True

    def _enabled_stops(self) -> list[_RingStop]:
        return [
            stop
            for stop in self._STOPS
            if self.settings.get(f"enable-{stop.key}", default=True)
        ]

    def _index_of_current(self, stops: list[_RingStop]) -> int:
        for i, stop in enumerate(stops):
            if stop.key == self._current_key:
                return i
        return -1

    def _current_stop(self) -> _RingStop | None:
        if self._current_key is None:
            return None

        for stop in self._enabled_stops():
            if stop.key == self._current_key:
                return stop

        # The previously selected stop is no longer enabled. Clear the selection instead of
        # silently falling back to some other stop the user didn't ask to adjust.
        self._current_key = None
        return None

    def _announce_stop(self, stop: _RingStop) -> None:
        if stop.kind in ("list", "cycle") and stop.key in self._list_selection:
            value: object = self._list_selection[stop.key]
        else:
            value = self.controller.get_value_internal(stop.module, stop.property)
        self.controller.present_message_internal(f"{stop.label}: {value}")

    def _cycle_stop(self, stop: _RingStop, direction: int) -> None:
        available = self._available_options(stop) if stop.kind == "list" else list(stop.values)
        if not available:
            self.controller.present_message_internal(
                f"No available options for {stop.label}."
            )
            return

        # Orca's own backend can overwrite the "current value" it reports for this property
        # as a side effect of unrelated speech (e.g. our own confirmation message below, which
        # is spoken in a different voice type). Track our last selection ourselves instead of
        # re-querying Orca, so cycling always advances regardless of what else has spoken.
        current = self._list_selection.get(stop.key)
        if current is None:
            current = cast(
                "str", self.controller.get_value_internal(stop.module, stop.property)
            )
        try:
            index = available.index(current)
        except ValueError:
            index = 0

        new_value = available[(index + direction) % len(available)]
        self.controller.set_value_internal(stop.module, stop.property, new_value)
        self._list_selection[stop.key] = new_value
        if stop.key == "synthesizer":
            # Available voices and voice sets depend on the active synthesizer.
            self._available_cache.clear()
        self.controller.present_message_internal(f"{stop.label}: {new_value}")

    def _available_options(self, stop: _RingStop) -> list[str]:
        if stop.key not in self._available_cache:
            raw_available = self.controller.get_value_internal(
                stop.module, stop.available_property
            )
            self._available_cache[stop.key] = (
                cast("list[str]", raw_available) if raw_available else []
            )
        return self._available_cache[stop.key]

    def _restore_persisted_values(self) -> None:
        if not self.settings.get(self._PERSIST_KEY, default=False):
            return

        values = self.settings.get(self._VALUES_KEY, default={})
        for stop in self._STOPS:
            value = values.get(stop.key)
            if value is None:
                continue
            self.controller.set_value_internal(stop.module, stop.property, value)
            if stop.kind in ("list", "cycle"):
                self._list_selection[stop.key] = value

    def _persist_current_value(self, stop: _RingStop) -> None:
        if not self.settings.get(self._PERSIST_KEY, default=False):
            return

        # For "list"/"cycle" stops, use our own tracked selection rather than re-querying Orca:
        # by this point our own confirmation message may already have clobbered the value Orca
        # reports back, for the same reason _cycle_stop tracks it itself.
        if stop.kind in ("list", "cycle"):
            value = self._list_selection.get(stop.key)
        else:
            value = self.controller.get_value_internal(stop.module, stop.property)
        if value is None:
            return

        values = self.settings.get(self._VALUES_KEY, default={})
        values[stop.key] = value
        self.settings.set(self._VALUES_KEY, values)

    def _get_keybinding(self, key: str) -> keybindings.KeyBinding:
        return keybindings.KeyBinding(key, keybindings.ORCA_MODIFIER_MASK)
