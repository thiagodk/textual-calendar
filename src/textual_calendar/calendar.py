
import locale
import re
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from typing import NamedTuple, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.events import Click
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.validation import Function, Number
from textual.widget import Widget
from textual.widgets import Button, Input, Label


class CalendarMonth(NamedTuple):
    """
    Hold some relevant information for monthrange function.
    """
    year: int
    month: int
    days_count: int

class CalendarDate(NamedTuple):
    """
    Hold internal selected date information for Calendar object.
    """
    year: int
    month: int
    day: Optional[int]


def _default_calendar_date() -> CalendarDate:
    today = date.today()
    return CalendarDate(today.year, today.month, None)


@dataclass
class _MonthRanges:
    """
    Hold information about previous, current and next month.
    """

    previous_month: CalendarMonth
    next_month: CalendarMonth
    first_weekday: int
    month_days: int

    @staticmethod
    def _monthrange(year: int, month: int) -> tuple[int, int]:
        """
        Correct version of monthrange function.

        This version of monthrange set Sunday as 1, Monday as 2, and so on...
        """
        weekday, month_days = monthrange(year, month)
        return ((weekday + 1) % 7 + 1, month_days)

    @classmethod
    def factory(cls, year: int, month: int) -> "_MonthRanges":
        """
        Create new instance of _MonthRanges based on selected month/year.

        :param year: Selected year.
        :param month: Selected month.
        """
        previous_month = month - 1
        previous_month_year = year
        if previous_month == 0:
            previous_month = 12
            previous_month_year -= 1
        previous_month_days = cls._monthrange(previous_month_year, previous_month)[1]
        next_month = month + 1
        next_month_year = year
        if next_month == 13:
            next_month = 1
            next_month_year += 1
        next_month_days = cls._monthrange(next_month_year, next_month)[1]
        first_weekday, month_days = cls._monthrange(year, month)
        return cls(
            CalendarMonth(previous_month_year, previous_month, previous_month_days),
            CalendarMonth(next_month_year, next_month, next_month_days),
            first_weekday, month_days)


class SelectCalendar(ModalScreen[Optional[CalendarDate]]):
    """
    Date selection dialog.

    Allow user to type an date arbitrarily.
    """

    DEFAULT_CSS = """
    SelectCalendar {
        align: center middle;
    }

    SelectCalendar > Vertical {
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        width: auto;
        height: auto;
    }

    SelectCalendar Horizontal {
        width: auto;
        height: auto;
        align: center middle;
    }

    #calendar-input-year {
        width: 5;
    }

    #calendar-input-month, #calendar-input-day {
        width: 3;
    }
    """

    BINDINGS = [
        ("up", "move_up()", "Increment"),
        ("down", "move_down()", "Decrement"),
        ("escape", "dismiss(None)", "Cancel"),
    ]

    input_year: Input
    input_month: Input
    input_day: Input

    def compose(self) -> ComposeResult:
        self.input_year = Input(
            placeholder="YYYY", type="integer", max_length=4, id="calendar-input-year",
            compact=True, validators=[Number(minimum=0, maximum=9999)],
            validate_on=["changed", "blur"])
        self.input_month = Input(
            placeholder="MM", type="integer", max_length=2, id="calendar-input-month",
            compact=True, validators=[Number(1, 12)],
            validate_on=["changed", "blur"])
        self.input_day = Input(
            placeholder="DD", type="integer", max_length=2, id="calendar-input-day",
            compact=True, validators=[Function(self.validate_day)],
            validate_on=["changed", "blur"])
        with Vertical():
            yield Horizontal(
                self.input_year,
                Label("/"),
                self.input_month,
                Label("/"),
                self.input_day)
            yield Horizontal(
                Button("Ok", id="calendar-input-ok", variant="success", flat=True),
                Button("Cancel", id="calendar-input-cancel", variant="warning", flat=True))

    def validate_day(self, value: str) -> bool:
        """
        Check for a valid day considering selected year/month.
        
        :param value: Input string of a day to be validate
        :return: Validation result, True if it's valid.
        """
        if len(value) == 0:
            return True
        try:
            year = int(self.input_year.value)
            month = int(self.input_month.value)
            day = int(value)
            date(year, month, day)
        except ValueError:
            return False
        return True

    def action_move_up(self) -> None:
        """
        Move focused input one unit ahead.
        """
        input_widget = self.focused
        if (not isinstance(input_widget, Input)
                or not input_widget.is_valid
                or not input_widget.value):
            return

        input_value = int(input_widget.value) + 1

        match input_widget.id:
            case "calendar-input-year":
                if input_value <= 9999:
                    input_widget.clear()
                    input_widget.insert(str(input_value), 0)

            case "calendar-input-month":
                if input_value <= 12:
                    input_widget.clear()
                    input_widget.insert(str(input_value), 0)

            case "calendar-input-day":
                year = self.query_one("#calendar-input-year", Input)
                month = self.query_one("#calendar-input-month", Input)
                if not year.is_valid or not month.is_valid:
                    return
                _, month_days = monthrange(int(year.value), int(month.value))
                if input_value <= month_days:
                    input_widget.clear()
                    input_widget.insert(str(input_value), 0)

    def action_move_down(self) -> None:
        """
        Move focused input one unit behind.
        """
        input_widget = self.focused
        if (not isinstance(input_widget, Input)
                or not input_widget.is_valid
                or not input_widget.value):
            return

        input_value = int(input_widget.value) - 1

        match input_widget.id:
            case "calendar-input-year":
                if input_value >= 0:
                    input_widget.clear()
                    input_widget.insert(str(input_value), 0)

            case "calendar-input-month" | "calendar-input-day":
                if input_value >= 1:
                    input_widget.clear()
                    input_widget.insert(str(input_value), 0)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle dialog button press event.
        """
        match event.button.id:
            case "calendar-input-ok":
                self.input_year.validate(self.input_year.value)
                self.input_month.validate(self.input_month.value)
                self.input_day.validate(self.input_day.value)

                if (self.input_year.is_valid and self.input_year.value
                        and self.input_month.is_valid and self.input_month.value
                        and self.input_day.is_valid):
                    self.dismiss(CalendarDate(
                        int(self.input_year.value),
                        int(self.input_month.value),
                        int(self.input_day.value) if self.input_day.value else None))

            case "calendar-input-cancel":
                self.dismiss(None)


class Calendar(Widget, can_focus=True):
    """
    Render a calendar for a selected month/year.
    """

    DEFAULT_CSS = """
    Calendar {
        layout: grid;
        height: auto;
        width: auto;
        grid-size: 7 8;
        grid-gutter: 0;
        grid-columns: 4;
        grid-rows: 1;
        border: round $secondary;
    }
    
    Calendar .calendar-header {
        text-align: center;
        color: $text;
        text-style: bold;
        column-span: 7;
        width: 100%;
    }

    Calendar .calendar-weekday {
        background: $accent;
        color: $text;
        text-style: bold;
        text-align: left;
    }

    Calendar .calendar-day {
        link-color: $text-primary;
        width: 100%;
        text-align: center;
        link-style: none;
    }

    Calendar .calendar-day-today {
        text-style: underline;
    }

    Calendar .calendar-day-selected {
        link-color: $text-success;
        background: $success-muted;
    }

    Calendar .calendar-day-prev-month,
    Calendar .calendar-day-next-month {
        link-color: $text-disabled;
    }
    """

    BINDINGS = [
        ("left", "previous_day()", "Previous Day"),
        ("right", "next_day()", "Next Day"),
        ("up", "previous_month()", "Previous Month"),
        ("down", "next_month()", "Next Month"),
        ("pageup", "previous_year()", "Previous Year"),
        ("pagedown", "next_year()", "Next Year"),
        ("insert", "input_calendar()", "Input Date"),
    ]

    calendar_date: reactive[CalendarDate] = reactive(_default_calendar_date)

    class Selected(Message):
        """Posted when the selected calendar date changes."""

        def __init__(self, calendar: "Calendar", date_value: date) -> None:
            super().__init__()
            self._calendar = calendar
            self.date = date_value

        @property
        def control(self) -> "Calendar":
            """Override Message control with correct parent type."""
            return self._calendar

    def compose(self) -> ComposeResult:
        yield Label('', classes="calendar-header")
        yield from [
            Label(
                locale.nl_langinfo(getattr(locale, f"ABDAY_{weekday}")),
                classes="calendar-weekday")
            for weekday in range(1, 8)
        ]

    @property
    def selected_date(self) -> Optional[date]:
        """
        Get native python date object for widget selected date.

        :return: Native date object or None if day is not selected.
        """
        if self.calendar_date.day is None:
            return None
        return date(self.calendar_date.year, self.calendar_date.month, self.calendar_date.day)

    @selected_date.setter
    def selected_date(self, date_value: date) -> None:
        """
        Set calendar to a specific data from python native date object.
        
        :param date_value: Python date object to set this calendar.
        """
        self.calendar_date = CalendarDate(date_value.year, date_value.month, date_value.day)

    async def _build_calendar(self) -> None:
        """
        Rebuild calendar days for selected month/year.
        """
        month_range = _MonthRanges.factory(self.calendar_date.year, self.calendar_date.month)
        today = date.today()

        # Set calendar header with the current Month/Year
        month_str = locale.nl_langinfo(getattr(locale, f"MON_{self.calendar_date.month}"))
        self.query_one(".calendar-header", Label).update(f'{month_str} {self.calendar_date.year}')

        # Remove current calendar days before build a new one
        await self.query(".calendar-day").remove()

        day_widgets: list[Label] = []

        # Add previous month's trailing days
        for day_offset in range(1, month_range.first_weekday):
            day_num = (
                month_range.previous_month.days_count
                - month_range.first_weekday
                + day_offset + 1)
            day = Label(
                f"{day_num:02}", id=("calendar-day-"
                    f"{month_range.previous_month.year}-"
                    f"{month_range.previous_month.month}-"
                    f"{day_num}"),
                classes="calendar-day calendar-day-prev-month")
            if date(
                    month_range.previous_month.year,
                    month_range.previous_month.month,
                    day_num) == today:
                day.add_class("calendar-day-today")
            day_widgets.append(day)

        # Add current month days
        current_month = (
            today.year == self.calendar_date.year
            and today.month == self.calendar_date.month)
        for day_num in range(1, month_range.month_days + 1):
            day = Label(
                f"{day_num:02}",
                id=f"calendar-day-{self.calendar_date.year}-{self.calendar_date.month}-{day_num}",
                classes="calendar-day")
            if current_month and day_num == today.day:
                day.add_class("calendar-day-today")
            if self.calendar_date.day == day_num:
                day.add_class("calendar-day-selected")
            day_widgets.append(day)

        # Add next month's leading days (to complete all 42 calendar cells)
        remaining_days = 42 - (month_range.first_weekday - 1 + month_range.month_days)
        for day_num in range(1, remaining_days + 1):
            day = Label(
                f"{day_num:02}", id=("calendar-day-"
                    f"{month_range.next_month.year}-"
                    f"{month_range.next_month.month}-"
                    f"{day_num}"),
                classes="calendar-day calendar-day-next-month")
            if date(month_range.next_month.year, month_range.next_month.month, day_num) == today:
                day.add_class("calendar-day-today")
            day_widgets.append(day)

        await self.mount_all(day_widgets)

    async def on_mount(self) -> None:
        """
        Run mount event to this widget.
        """
        await self._build_calendar()

    def on_click(self, event: Click) -> None:
        """
        Handle mouse clicks on calendar.
        """
        day, _ = self.screen.get_widget_at(*event.screen_offset)

        if isinstance(day, Label) and "calendar-day" in day.classes and day.id is not None:
            m = re.fullmatch(r"calendar-day-(\d+)-(\d+)-(\d+)", day.id)
            if m:
                event.stop()
                self.action_select_calendar(int(m[1]), int(m[2]), int(m[3]))

    def action_input_calendar(self) -> None:
        """
        Action to open calendar input modal screen.
        """
        def _update_calendar_from_input(selected_calendar: Optional[CalendarDate]) -> None:
            if selected_calendar is not None:
                self.calendar_date = selected_calendar
        select_calendar_screen = SelectCalendar()
        self.app.push_screen(select_calendar_screen, _update_calendar_from_input)

    def action_select_calendar(self, year: int, month: int, day: int) -> None:
        """
        Action to move selected date to an arbitrary date.

        Opposed to `action_select_day`, this action can be used to move selected day to another
        month/year.
        
        :param year: Selected year.
        :param month: Selected month.
        :param day: Selected day.
        """
        try:
            date(year, month, day)  # Only checking if date is valid.
        except ValueError:
            pass  # Otherwise ignore it.
        else:
            self.calendar_date = CalendarDate(year, month, day)

    def action_select_day(self, day: int) -> None:
        """
        Action to move selected date to a specific day.
        
        :param day: Selected day.
        """
        try:
            date(self.calendar_date.year, self.calendar_date.month, day)
        except ValueError:
            pass
        else:
            self.calendar_date = CalendarDate(
                self.calendar_date.year, self.calendar_date.month, day)

    def action_previous_day(self) -> None:
        """
        Action to move selected date to the previous day.
        """
        prev_date = self.selected_date
        if prev_date is not None:
            prev_date -= timedelta(days=1)
            self.calendar_date = CalendarDate(prev_date.year, prev_date.month, prev_date.day)

    def action_next_day(self) -> None:
        """
        Action to move selected date to the next day.
        """
        next_date = self.selected_date
        if next_date is not None:
            next_date += timedelta(days=1)
            self.calendar_date = CalendarDate(next_date.year, next_date.month, next_date.day)

    def action_previous_month(self) -> None:
        """
        Action to move selected date to the previous month.
        """
        year = self.calendar_date.year
        month = self.calendar_date.month - 1
        day = self.calendar_date.day

        if month == 0:
            month = 12
            year -= 1

        if day is not None:
            # Check if we can move same day over the previous month
            _, month_days = monthrange(year, month)
            day = min(day, month_days)

        self.calendar_date = CalendarDate(year, month, day)

    def action_next_month(self) -> None:
        """
        Action to move selected date to the next month.
        """
        year = self.calendar_date.year
        month = self.calendar_date.month + 1
        day = self.calendar_date.day

        if month == 13:
            month = 1
            year += 1

        if day is not None:
            # Check if we can move same day over the next month
            _, month_days = monthrange(year, month)
            day = min(day, month_days)

        self.calendar_date = CalendarDate(year, month, day)

    def action_previous_year(self) -> None:
        """
        Action to move selected date to the previous year.
        """
        year = self.calendar_date.year - 1
        month = self.calendar_date.month
        day = self.calendar_date.day

        if day is not None:
            # We have to do this because of leap years
            _, month_days = monthrange(year, month)
            day = min(day, month_days)

        self.calendar_date = CalendarDate(year, month, day)

    def action_next_year(self) -> None:
        """
        Action to move selected date to the next year.
        """
        year = self.calendar_date.year + 1
        month = self.calendar_date.month
        day = self.calendar_date.day

        if day is not None:
            # We have to do this because of leap years
            _, month_days = monthrange(year, month)
            day = min(day, month_days)

        self.calendar_date = CalendarDate(year, month, day)

    async def watch_calendar_date(self, old_date: CalendarDate, new_date: CalendarDate) -> None:
        """
        Watch for changes in selected date.
        
        :param old_date: Previous date before changing.
        :param new_date: New changed date.
        """
        if old_date != new_date:
            date_value = self.selected_date
            if date_value is not None:
                self.post_message(self.Selected(self, date_value))
            if old_date.year != new_date.year or old_date.month != new_date.month:
                await self._build_calendar()
            elif new_date.day is not None:
                self.query(".calendar-day").remove_class("calendar-day-selected")
                try:
                    day = self.get_child_by_id(
                        f"calendar-day-{new_date.year}-{new_date.month}-{new_date.day}")
                except NoMatches:
                    await self._build_calendar()
                else:
                    day.add_class("calendar-day-selected")
