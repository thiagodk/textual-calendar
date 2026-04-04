
from datetime import date, time
from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.containers import Grid, Vertical
from textual.widgets import Label

from .base import ExampleApp
from ..datetime import DatetimePicker


class DatetimeApp(ExampleApp):
    """
    Example use of DatetimePicker widget.
    """

    CSS = """
    .datetime-container {
        align: center top;
        padding: 2;
        width: 100%;
        height: auto;
    }

    .info-grid {
        layout: grid;
        grid-size: 2 2;
        grid-columns: auto 1fr;
        width: 60;
        height: auto;
        margin-top: 2;
    }

    .info-grid Label.key {
        text-align: right;
        padding-right: 1;
        height: 1;
    }

    .info-grid Label.value {
        text-align: left;
        height: 1;
    }    """

    def compose(self) -> ComposeResult:
        with Vertical(classes="datetime-container"):
            yield DatetimePicker(show_tz=True, id="datetime")
        with Grid(classes="info-grid"):
            yield Label("Date:", classes="key")
            yield Label(classes="value", id="date-value")
            yield Label("Time:", classes="key")
            yield Label(classes="value", id="time-value")

    def on_mount(self) -> None:
        """
        Event handler called when app is mounted.
        """
        datetime_obj = self.query_one("#datetime", DatetimePicker)
        self.query_one("#date-value", Label).update(self.print_date(datetime_obj.date_value))
        self.query_one("#time-value", Label).update(self.print_time(datetime_obj.time_value))

    @staticmethod
    def print_date(date_value: Optional[date]) -> str:
        """
        Get a label content from date object.
        """
        if date_value is None:
            return ""
        return date_value.strftime("%Y-%m-%d")

    @staticmethod
    def print_time(time_value: Optional[time]) -> str:
        """
        Get a label content from time object.
        """
        if time_value is None:
            return ""
        output = time_value.strftime("%H:%M:%S")
        if time_value.tzinfo is not None:
            output += f" {time_value.tzinfo}"
        return output

    @on(DatetimePicker.Changed, "#datetime")
    def update_datetime_label(self, message: DatetimePicker.Changed) -> None:
        """
        Update testing labels when date or time value changes.
        """
        match message.obj_change:
            case "date":
                self.query_one("#date-value", Label).update(
                    self.print_date(message.datetime_picker.date_value))
            case "time":
                self.query_one("#time-value", Label).update(
                    self.print_time(message.datetime_picker.time_value))
