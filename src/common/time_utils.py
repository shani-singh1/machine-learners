from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterator


@dataclass(frozen=True)
class MonthWindow:
    year: int
    month: int
    start_date: date
    end_date: date

    @property
    def year_month(self) -> str:
        return f"{self.year:04d}_{self.month:02d}"


def iter_month_windows(start: date, end: date) -> Iterator[MonthWindow]:
    current = date(start.year, start.month, 1)
    while current <= end:
        if current.month == 12:
            next_month = date(current.year + 1, 1, 1)
        else:
            next_month = date(current.year, current.month + 1, 1)

        month_end = min(end, date.fromordinal(next_month.toordinal() - 1))
        if month_end >= start:
            yield MonthWindow(
                year=current.year,
                month=current.month,
                start_date=max(start, current),
                end_date=month_end,
            )

        current = next_month
