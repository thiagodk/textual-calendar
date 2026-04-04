from datetime import date as py_date, datetime as py_datetime, time as py_time
from typing import Any, Literal, Optional

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget

from .calendar import Calendar
from .time import Time

class DatetimePicker(Widget, can_focus=True):
    """
    Render a calendar with clock for datetime picking.
    """

    calendar: Calendar
    time: Time

    DEFAULT_CSS = """
    DatetimePicker {
        width: auto;
        height: auto;
        border: round $secondary;
    }

    DatetimePicker Vertical {
        width: auto;
        height: auto;
        align: center top;
    }

    DatetimePicker Calendar {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("tab", "focus_next", "Focus Next"),
        ("shift+tab", "focus_previous", "Focus Previous"),
    ]

    class Changed(Message):
        """Posted when time or calendar date changes."""

        def __init__(
            self,
            datetime_picker: "DatetimePicker",
            obj_change: Literal["date", "time"],
        ) -> None:
            super().__init__()
            self.datetime_picker = datetime_picker
            self.obj_change = obj_change

        @property
        def control(self) -> "DatetimePicker":
            """Override Message control with correct parent type."""
            return self.datetime_picker

    def __init__(
        self,
        *children: Widget,
        initial_datetime: Optional[py_datetime] = None,
        show_tz: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*children, **kwargs)
        self.initial_datetime = initial_datetime
        self._show_tz = show_tz

    def compose(self) -> ComposeResult:
        with Vertical():
            if self.initial_datetime is None:
                initial_date = None
                initial_time = None
            else:
                initial_date = self.initial_datetime.date()
                initial_time = self.initial_datetime.time()
            self.calendar = Calendar(initial_date=initial_date)
            self.time = Time(initial_time=initial_time, show_tz=self._show_tz)
            yield self.calendar
            yield self.time

    def on_calendar_selected(self, _: Calendar.Selected) -> None:
        """
        Handle date changes in the calendar.
        """
        self.post_message(self.Changed(self, "date"))

    def on_time_changed(self, _: Time.Changed) -> None:
        """
        Handle time changes in the clock.
        """
        self.post_message(self.Changed(self, "time"))

    @property
    def date_value(self) -> Optional[py_date]:
        """
        Get date portion of DatetimePicker.

        :return: Python native `date` object from selected date in
            Calendar widget.
        """
        if not getattr(self, "calendar", None):
            return None
        return self.calendar.selected_date

    @date_value.setter
    def date_value(self, new_date: py_date) -> None:
        """
        Set date value of DatetimePicker Widget.

        :param new_date: Set date of DatetimePicker to this date.
        """
        if not getattr(self, "calendar", None):
            return
        self.calendar.selected_date = new_date

    @property
    def time_value(self) -> Optional[py_time]:
        """
        Get time portion of DatetimePicker.
        
        :return: Python native `time` object from selected date in
            Time Widget.
        """
        if not getattr(self, "time", None):
            return None
        return self.time.time_value

    @time_value.setter
    def time_value(self, new_time: py_time) -> None:
        """
        Set time value of DatetimePicker Widget.

        :param new_time: Set time of DatetimePicker to this time.
        """
        if not getattr(self, "time", None):
            return
        self.time.time_value = new_time

    @property
    def datetime_value(self) -> Optional[py_datetime]:
        """
        Get a full datetime object from DatetimePicker Widget.

        :return: Python native `datetime` object from combination of
            Calendar and Time widgets.
        """
        date_val = self.date_value
        time_val = self.time_value
        if date_val is None or time_val is None:
            return None
        return py_datetime.combine(date_val, time_val)

    @datetime_value.setter
    def datetime_value(self, new_datetime: py_datetime) -> None:
        """
        Set date and time of DatetimePicker widget.

        :param new_datetime: Set date and time of DatetimePicker from this
            datetime object.
        """
        self.date_value = new_datetime.date()
        self.time_value = new_datetime.time()
