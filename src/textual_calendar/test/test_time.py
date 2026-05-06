from datetime import time
from typing import Any, Optional
from zoneinfo import ZoneInfo

import pytest
from textual.app import App, ComposeResult
from textual.pilot import Pilot
from textual.widgets import Digits

from textual_calendar.time import Time


class AppInit(App[Any]):
    """Test app with initial time."""

    def __init__(self, show_tz: bool, *args: Any, **kwargs: Any):
        self._show_tz = show_tz
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose time widget with initial time."""
        yield Time(initial_time=time(12, 30, 0), show_tz=self._show_tz)


class AppNonInit(App[Any]):
    """Test app without initial time."""

    def __init__(self, show_tz: bool, *args: Any, **kwargs: Any):
        self._show_tz = show_tz
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose time widget without initial time."""
        yield Time(show_tz=self._show_tz)


@pytest.mark.parametrize("show_tz", [True, False])
@pytest.mark.asyncio
async def test_time_initialization(show_tz: bool) -> None:
    """Test time initialization with and without timezone support."""
    app = AppNonInit(show_tz=show_tz)

    async with app.run_test():
        _time = app.query_one("Time", Time)
        assert _time.clock.hour.value == "00"
        assert _time.clock.minute.value == "00"
        assert _time.clock.second.value == "00"
        if show_tz:
            assert _time.tz is not None
        else:
            assert _time.tz is None


@pytest.mark.parametrize("tz", [None, "America/New_York"])
@pytest.mark.asyncio
async def test_time_app(tz: Optional[str]) -> None:
    """Test time widget interaction and timezone support."""
    app = AppInit(show_tz=tz is not None)

    async with app.run_test() as pilot:
        _time = app.query_one("Time", Time)

        # Test initial state
        await _test_initial_state(_time)

        # Test hour manipulation
        await _test_hour_manipulation(pilot, _time)

        # Test minute manipulation
        await _test_minute_manipulation(pilot, _time)

        # Test second manipulation
        await _test_second_manipulation(pilot, _time)

        # Test timezone if applicable
        if tz is not None:
            await _test_timezone_selection(pilot, app, _time, tz)
        else:
            assert len(app.query("#time-tz")) == 0


def _check_selected_time(app: App[Any], expected_id: str) -> None:
    """Check which time field is currently selected."""
    query_results = app.query("Digits.time-number-selected")
    assert len(query_results) == 1
    time_number = query_results[0]
    assert isinstance(time_number, Digits)
    assert time_number.id == expected_id


async def _test_initial_state(_time: Time) -> None:
    """Test the initial state of the time widget."""
    assert _time.time_value == time(12, 30, 0)
    assert _time.time_str == "12:30:00"


async def _test_hour_manipulation(pilot: Pilot[Any], _time: Time) -> None:
    """Test hour field manipulation."""
    assert len(pilot.app.query("Digits.time-number-selected")) == 0
    await pilot.press("right")
    _check_selected_time(pilot.app, "time-hour")
    for _ in range(3):
        await pilot.press("up")
    assert _time.time_value == time(15, 30, 0)
    assert _time.time_str == "15:30:00"


async def _test_minute_manipulation(pilot: Pilot[Any], _time: Time) -> None:
    """Test minute field manipulation."""
    await pilot.press("right")
    _check_selected_time(pilot.app, "time-minute")
    for _ in range(5):
        await pilot.press("down")
    assert _time.time_value == time(15, 25, 0)
    assert _time.time_str == "15:25:00"


async def _test_second_manipulation(pilot: Pilot[Any], _time: Time) -> None:
    """Test second field manipulation with various operations."""
    await pilot.press("right")
    _check_selected_time(pilot.app, "time-second")

    # Single digit input
    await pilot.press("1")
    await pilot.press("right")
    assert len(pilot.app.query("Digits.time-number-selected")) == 0
    assert _time.time_value == time(15, 25, 1)
    assert _time.time_str == "15:25:01"

    # Increment operation
    await pilot.press("left")
    _check_selected_time(pilot.app, "time-second")
    await pilot.press("2")
    for _ in range(2):
        await pilot.press("up")
    await pilot.press("right")
    assert len(pilot.app.query("Digits.time-number-selected")) == 0
    assert _time.time_value == time(15, 25, 4)
    assert _time.time_str == "15:25:04"

    # Another increment
    await pilot.press("left")
    _check_selected_time(pilot.app, "time-second")
    await pilot.press("2")
    for _ in range(5):
        await pilot.press("up")
    await pilot.press("right")
    assert len(pilot.app.query("Digits.time-number-selected")) == 0
    assert _time.time_value == time(15, 25, 5)
    assert _time.time_str == "15:25:05"

    # Two digit input
    await pilot.press("left")
    _check_selected_time(pilot.app, "time-second")
    await pilot.press("4", "5")
    assert len(pilot.app.query("Digits.time-number-selected")) == 0
    assert _time.time_value == time(15, 25, 45)
    assert _time.time_str == "15:25:45"

    # Test overflow protection
    await pilot.press("left")
    _check_selected_time(pilot.app, "time-second")
    for _ in range(15):  # Check if digits do not overflow
        await pilot.press("up")
    assert _time.time_value == time(15, 25, 59)
    assert _time.time_str == "15:25:59"
    assert _time.time_value.tzinfo is None


async def _test_timezone_selection(pilot: Pilot[Any], app: App[Any], _time: Time, tz: str) -> None:
    """Test timezone selection functionality."""
    assert len(app.query("#time-tz")) == 1
    await pilot.click("#time-tz")
    await pilot.press(*list(tz))
    assert _time.time_value is not None
    assert _time.time_value.tzinfo == ZoneInfo(tz)
