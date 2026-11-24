"""Типы данных MOEX ISS."""

from typing import Literal

type Values = str | int | float | None
type TableRow = dict[str, Values]
type Table = list[TableRow]
type TablesDict = dict[str, Table]
type WebQuery = dict[str, str | int]

type Interval = Literal[1, 10, 60, 24, 7, 31, 4]
type BoardTable = Literal["securities", "marketdata"]
type EngineTable = Literal["dailytable", "timetable", "engine"]
type ReferencePlaceholder = Literal[
    "engines",
    "markets",
    "boards",
    "boardgroups",
    "durations",
    "securitytypes",
    "securitygroups",
    "securitycollections",
]
