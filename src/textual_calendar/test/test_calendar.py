from datetime import date
from typing import Any

import pytest
from textual.app import App, ComposeResult

from textual_calendar.calendar import Calendar, SelectCalendar


class AppInit(App[Any]):
    """Test app with initial date."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.test_dates = [
            date(2025, 12, 25),
            date(2025, 12, 24),
            date(2025, 11, 24),
            date(2024, 11, 24),
            date(2022, 4, 1),
            date(2022, 4, 2),
            date(2022, 5, 2),
            date(2023, 5, 2),
            date(2023, 5, 31),
            date(2023, 4, 30),
            date(2021, 6, 3)
        ]
        self._test_position = 0
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose calendar widget with initial date."""
        yield Calendar(initial_date=date(2025, 12, 25))

    def on_calendar_selected(self, message: Calendar.Selected) -> None:
        """Handle calendar selection events."""
        assert message.date == self.test_dates[self._test_position]
        self._test_position += 1


class AppNonInit(App[Any]):
    """Test app without initial date."""

    def compose(self) -> ComposeResult:
        """Compose calendar widget without initial date."""
        yield Calendar()


@pytest.mark.asyncio
async def test_calendar_initialization() -> None:
    """Test calendar initialization with default values."""
    app = AppNonInit()

    async with app.run_test():
        calendar = app.query_one("Calendar", Calendar)
        assert calendar.calendar_date.year == date.today().year
        assert calendar.calendar_date.month == date.today().month


@pytest.mark.asyncio
async def test_calendar_app() -> None:
    """Test calendar navigation and date selection."""
    app = AppInit()
    async with app.run_test() as pilot:
        calendar = app.query_one("Calendar", Calendar)
        assert calendar.selected_date == app.test_dates[0]
        await pilot.press("left")
        assert calendar.selected_date == app.test_dates[1]
        await pilot.press("up")
        assert calendar.selected_date == app.test_dates[2]
        await pilot.press("pageup")
        assert calendar.selected_date == app.test_dates[3]
        await pilot.press("insert")
        # Manipulate date into insert date modal
        await pilot.press("2", "0", "2", "1")
        await pilot.press("up")
        await pilot.press("tab")
        await pilot.press("0", "4")
        await pilot.press("tab")
        await pilot.press("0", "1")
        await pilot.click("#calendar-input-ok")
        assert calendar.selected_date == app.test_dates[4]
        await pilot.press("right")
        assert calendar.selected_date == app.test_dates[5]
        await pilot.press("down")
        assert calendar.selected_date == app.test_dates[6]
        await pilot.press("pagedown")
        assert calendar.selected_date == app.test_dates[7]
        calendar.action_select_day(31)
        assert calendar.selected_date == app.test_dates[8]
        await pilot.press("up")
        assert calendar.selected_date == app.test_dates[9]
        calendar.action_select_day(31)  # Expected to be ignored as April don't have 31st
        assert calendar.selected_date == app.test_dates[9]
        await pilot.press("insert")
        # Try to input an invalid date into insert date modal
        await pilot.press("2", "0", "2", "6")
        await pilot.click("#calendar-input-month")
        await pilot.press("1", "3")
        await pilot.click("#calendar-input-day")
        await pilot.press("3", "2")
        await pilot.click("#calendar-input-ok")
        assert isinstance(app.screen, SelectCalendar)
        await pilot.click("#calendar-input-cancel")
        assert not isinstance(app.screen, SelectCalendar)
        assert calendar.selected_date == app.test_dates[9]
        calendar.selected_date = date(2021, 6, 3)
        assert calendar.selected_date == app.test_dates[10]
