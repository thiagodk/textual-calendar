
from datetime import time
from typing import Literal, NamedTuple, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Digits


class ClockDigits(NamedTuple):
    """
    Set of Digits Widgets to represent a clock time.
    """
    hour: Digits
    minute: Digits
    second: Digits


class Time(Widget, can_focus=True):
    """
    Render a clock for time selection.
    """

    DEFAULT_CSS = """
    Time {
        height: auto;
        width: auto;
        border: round $secondary;
        padding: 1 2;
    }

    Time Vertical {
        height: auto;
        width: auto;
    }

    Time Horizontal {
        height: auto;
        width: auto;
    }

    Time Digits {
        color: $text;
        width: auto;
        border-bottom: blank;
        border-top: blank;
    }

    Time Digits.time-number-selected {
        background: $success-muted;
        color: $success;
        border-bottom: solid $secondary;
    }
    """

    BINDINGS = [
        ("left", "move_previous()", "Move to the previous digit"),
        ("right", "move_next()", "Move to the next digit"),
        ("up", "move_up()", "Next clock digit"),
        ("down", "move_down()", "Previous clock digit"),
        ("0", "set_digit(0)", "Set digit to 0 at the selected clock position"),
        ("1", "set_digit(1)", "Set digit to 1 at the selected clock position"),
        ("2", "set_digit(2)", "Set digit to 2 at the selected clock position"),
        ("3", "set_digit(3)", "Set digit to 3 at the selected clock position"),
        ("4", "set_digit(4)", "Set digit to 4 at the selected clock position"),
        ("5", "set_digit(5)", "Set digit to 5 at the selected clock position"),
        ("6", "set_digit(6)", "Set digit to 6 at the selected clock position"),
        ("7", "set_digit(7)", "Set digit to 7 at the selected clock position"),
        ("8", "set_digit(8)", "Set digit to 8 at the selected clock position"),
        ("9", "set_digit(9)", "Set digit to 9 at the selected clock position"),
    ]

    clock: ClockDigits

    last_time_value: reactive[time] = reactive(time)

    class Changed(Message):
        """Posted when time in the clock changes."""

        def __init__(self, time_obj: "Time", time_value: time):
            super().__init__()
            self.time_obj: Time = time_obj
            self.time_value: time = time_value

        @property
        def control(self) -> "Time":
            """Override Message control with correct parent type."""
            return self.time_obj

    @property
    def time_str(self) -> Optional[str]:
        """
        Convert time object to output string.
        """
        time_value = self.time_value
        if time_value is None:
            return None
        return time_value.strftime("%H:%M:%S")

    @property
    def time_value(self) -> Optional[time]:
        """
        Convert widget to time object.
        """
        hour = self.get_widget_by_id("time-hour", Digits)
        minute = self.get_widget_by_id("time-minute", Digits)
        second = self.get_widget_by_id("time-second", Digits)
        if hour.value.endswith("-") or minute.value.endswith("-") or second.value.endswith("-"):
            return None
        try:
            return time(int(hour.value), int(minute.value), int(second.value))
        except ValueError:
            return None

    def compose(self) -> ComposeResult:
        self.clock = ClockDigits(
            Digits("00", classes="time-number", id="time-hour"),
            Digits("00", classes="time-number", id="time-minute"),
            Digits("00", classes="time-number", id="time-second"))
        with Vertical():
            yield Horizontal(
                self.clock.hour,
                Digits(":"),
                self.clock.minute,
                Digits(":"),
                self.clock.second)

    @staticmethod
    def move_time(time_number: Digits, direction: Literal["up", "down"]) -> Optional[str]:
        """
        Increment/Decrement selected digit by one.
        
        Apply same logic as "move_time_at" function.

        :param direction: If "up" it will increment, if "down" it will decrement.
        :return: New time object after digit change, or None if digit change result in an invalid
            time string.
        """
        if time_number.value.endswith("-"):
            first_digit = int(time_number.value[0])
            match direction:
                case "up":
                    first_digit += 1
                    if (time_number.id == "time-hour" and first_digit > 2) or first_digit > 5:
                        return None

                case "down":
                    first_digit -= 1
                    if first_digit < 0:
                        return None
            return f"{first_digit}-"

        time_value = int(time_number.value)
        match direction:
            case "up":
                time_value += 1
                if (time_number.id == "time-hour" and time_value > 23) or time_value > 59:
                    return None

            case "down":
                time_value -= 1
                if time_value < 0:
                    return None
        return f"{time_value:02}"

    @staticmethod
    def set_time_digit(time_number: Digits, digit: int) -> Optional[str]:
        """
        Set a digit number into selected Digits Widget.
        
        :param digit: Digit to be set.
        :return: New time object after digit change, or None if digit change result in an invalid
            time string.
        """
        if digit < 0 or digit > 9:
            return None  # Digit cannot be negative or multi-digit number.
        if time_number.value.endswith("-"):
            # Input second digit
            first_digit = time_number.value[0]
            if time_number.id == "time-hour" and first_digit == "2" and digit > 3:
                return None  # Get hour higher than 23
            return f"{first_digit}{digit}"
        if time_number.id == "time-hour" and digit > 2:
            return None
        if digit > 5:
            return None
        return f"{digit}-"

    def _update_time_if_changed(self) -> None:
        """
        Update the last_time_value if the current time has changed.
        """
        time_value = self.time_value
        if time_value is not None and time_value != self.last_time_value:
            self.last_time_value = time_value

    def on_click(self, event: Click) -> None:
        """
        Handle mouse clicks on clock digits.
        """
        time_number, _ = self.screen.get_widget_at(*event.screen_offset)
        valid_time_id = ("time-hour", "time-minute", "time-second")
        query = self.query("Digits.time-number-selected")
        selected_time_number = query[0] if len(query) else None

        if isinstance(time_number, Digits) and (
                "time-number" in time_number.classes and
                time_number.id in valid_time_id):
            event.stop()
            if selected_time_number is not None and selected_time_number != time_number:
                assert isinstance(selected_time_number, Digits)
                self._remove_selection(selected_time_number)
                time_number.add_class("time-number-selected")
        elif selected_time_number is not None:
            # Deselect clock digit if click in somewhere else
            assert isinstance(selected_time_number, Digits)
            self._remove_selection(selected_time_number)

    def action_move_up(self) -> None:
        """
        Action to increment current selected digit in the clock.
        """
        query = self.query("Digits.time-number-selected")
        if len(query) == 1:
            time_number = query[0]
            assert isinstance(time_number, Digits)
            time_value = self.move_time(time_number, "up")
            if time_value is not None:
                time_number.update(time_value)
                self._update_time_if_changed()

    def action_move_down(self) -> None:
        """
        Action to decrement current selected digit in the clock.
        """
        query = self.query("Digits.time-number-selected")
        if len(query) == 1:
            time_number = query[0]
            assert isinstance(time_number, Digits)
            time_value = self.move_time(time_number, "down")
            if time_value is not None:
                time_number.update(time_value)
                self._update_time_if_changed()

    def _remove_selection(self, time_number: Digits) -> None:
        """
        Remove Digit selection.

        :param time_number: Digit Widget to remove selection.
        """
        if time_number.value.endswith("-"):
            time_number.update(f"0{time_number.value[0]}")
            self._update_time_if_changed()
        time_number.remove_class("time-number-selected")

    def action_move_previous(self) -> None:
        """
        Action to move backward selected clock digit position.
        """
        query = self.query("Digits.time-number-selected")
        match len(query):
            case 0:
                self.get_widget_by_id("time-second").add_class("time-number-selected")
            case 1:
                time_number = query[0]
                assert isinstance(time_number, Digits)
                self._remove_selection(time_number)
                match time_number.id:
                    case "time-second":
                        self.get_widget_by_id("time-minute").add_class("time-number-selected")
                    case "time-minute":
                        self.get_widget_by_id("time-hour").add_class("time-number-selected")

    def action_move_next(self) -> None:
        """
        Action to move forward selected clock digits.
        """
        query = self.query("Digits.time-number-selected")
        match len(query):
            case 0:
                self.get_widget_by_id("time-hour").add_class("time-number-selected")
            case 1:
                time_number = query[0]
                assert isinstance(time_number, Digits)
                self._remove_selection(time_number)
                match time_number.id:
                    case "time-hour":
                        self.get_widget_by_id("time-minute").add_class("time-number-selected")
                    case "time-minute":
                        self.get_widget_by_id("time-second").add_class("time-number-selected")

    def action_set_digit(self, digit: int) -> None:
        """
        Action to arbitrarily set a digit number to select clock digits.
        
        :param digit: Digit number to be set.
        """
        assert 0 <= digit <= 9
        query = self.query("Digits.time-number-selected")
        if len(query) == 1:
            time_number = query[0]
            assert isinstance(time_number, Digits)
            time_value = self.set_time_digit(time_number, digit)
            if time_value is not None:
                time_number.update(time_value)
                self._update_time_if_changed()
                if not time_value.endswith("-"):
                    self.action_move_next()

    def watch_last_time_value(self, old_time: time, new_time: time) -> None:
        """
        Watch for time changes.

        :param old_time: Previous time before change.
        :param new_time: New changed time.
        """
        if old_time != new_time:
            self.post_message(self.Changed(self, new_time))
