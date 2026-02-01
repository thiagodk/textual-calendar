
import locale
import re
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from typing import NamedTuple, Optional

from textual.app import ComposeResult
from textual.css.query import NoMatches
from textual.events import Click
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


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
