"""Тесты для разнообразных запросов."""

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import pytest
from requests import Session

from apimoex import client, requests

if TYPE_CHECKING:
    from collections.abc import Iterator

_CA_BUNDLE = Path(__file__).parent / "certs" / "russian_trusted_root_ca.pem"


@pytest.fixture(scope="module", name="session")
def make_session() -> Iterator[Session]:
    """Создание http сессии с корневым сертификатом MOEX."""
    with Session() as session:
        session.verify = str(_CA_BUNDLE)
        yield session


def test_make_query_empty() -> None:
    query = requests._make_query()  # pyright: ignore[reportPrivateUsage]
    assert query == {}


def test_make_query_full() -> None:
    query = requests._make_query(  # pyright: ignore[reportPrivateUsage]
        q="GAZP",
        interval=60,
        start="2019-10-09",
        end="2019-11-12",
        table="new_table",
        columns=("4", "a"),
    )
    assert isinstance(query, dict)
    assert len(query) == 6
    assert query["q"] == "GAZP"
    assert query["interval"] == 60
    assert query["from"] == "2019-10-09"
    assert query["till"] == "2019-11-12"
    assert query["iss.only"] == "new_table,history.cursor"
    assert query["new_table.columns"] == "4,a"


def test_get_table() -> None:
    table = requests._get_table({"a": [{"b": "c"}]}, "a")  # pyright: ignore[reportPrivateUsage]
    assert table == [{"b": "c"}]


def test_get_table_notable() -> None:
    with pytest.raises(client.ISSTableNotFoundError) as error:
        _ = requests._get_table({"a": []}, "b")  # pyright: ignore[reportPrivateUsage]
    assert "Table b is missing in the response" in str(error.value)


def test_get_reference(session: Session) -> None:
    data = requests.get_reference(session, "engines")
    assert isinstance(data, list)
    assert len(data) >= 10


check_points = [
    ("1-02-65104-D", {"UPRO", "EONR", "OGK4"}),
    ("10301481B", {"SBER", "SBER03"}),
    ("20301481B", {"SBERP", "SBERP03"}),
    ("1-02-06556-A", {"PHOR"}),
]


@pytest.mark.parametrize(("reg_number", "expected"), check_points)
def test_find_securities(session: Session, reg_number: str, expected: set[str]) -> None:
    data = requests.find_securities(session, reg_number)
    assert isinstance(data, list)
    assert expected == {row["secid"] for row in data if row["regnumber"] == reg_number}


def test_find_security_description(session: Session) -> None:
    data = requests.find_security_description(session, "IRAO")
    assert isinstance(data, list)
    assert len(data) >= 19


def test_get_market_candle_borders(session: Session) -> None:
    data = requests.get_market_candle_borders(session, "SNGSP")
    assert isinstance(data, list)
    assert len(data) == 7
    for i in data:
        del i["end"]
    assert data == [
        {"begin": "2011-12-15 10:00:00", "interval": 1, "board_group_id": 57},
        {"begin": "2003-07-01 00:00:00", "interval": 4, "board_group_id": 57},
        {"begin": "2003-07-28 00:00:00", "interval": 7, "board_group_id": 57},
        {"begin": "2011-12-08 10:00:00", "interval": 10, "board_group_id": 57},
        {"begin": "2003-07-31 00:00:00", "interval": 24, "board_group_id": 57},
        {"begin": "2003-07-01 00:00:00", "interval": 31, "board_group_id": 57},
        {"begin": "2011-11-17 10:00:00", "interval": 60, "board_group_id": 57},
    ]


def test_get_board_candle_borders(session: Session) -> None:
    data = requests.get_board_candle_borders(session, "UPRO")
    assert isinstance(data, list)
    assert len(data) == 7
    for i in data:
        del i["end"]
    assert data == [
        {"begin": "2016-07-01 09:59:00", "interval": 1},
        {"begin": "2016-07-01 00:00:00", "interval": 4},
        {"begin": "2016-06-27 00:00:00", "interval": 7},
        {"begin": "2016-07-01 09:50:00", "interval": 10},
        {"begin": "2016-07-01 00:00:00", "interval": 24},
        {"begin": "2016-07-01 00:00:00", "interval": 31},
        {"begin": "2016-07-01 09:00:00", "interval": 60},
    ]


def test_get_market_candles_from_beginning(session: Session) -> None:
    data = requests.get_market_candles(session, "RTKM", interval=1, end="2011-12-16")
    assert isinstance(data, list)
    assert len(data) > 500
    df = pd.DataFrame(data)
    assert df.columns.size == 7
    assert df.loc[0, "open"] == pytest.approx(141.55)
    assert df.loc[1, "close"] == pytest.approx(141.59)
    assert df.loc[2, "high"] == pytest.approx(142.4)
    assert df.loc[3, "low"] == pytest.approx(140.81)
    assert df.loc[4, "value"] == pytest.approx(2_586_296.9)
    assert df.loc[6, "begin"] == "2011-12-15 10:06:00"


def test_get_market_candles_to_end(session: Session) -> None:
    data = requests.get_market_candles(session, "LSRG", interval=24, start="2020-08-20")
    assert isinstance(data, list)
    assert len(data) > 13
    assert len(data[0]) == 7
    assert data[0]["open"] == pytest.approx(775.4)
    assert data[1]["close"] == pytest.approx(771.8)
    assert data[2]["high"] == pytest.approx(779.8)
    assert data[3]["low"] == pytest.approx(770.2)
    assert data[4]["value"] == pytest.approx(59495740.6)
    assert data[6]["begin"] == "2020-08-28 00:00:00"


def test_get_market_candles_empty_history(session: Session) -> None:
    data = requests.get_market_candles(session, "KSGR", interval=24)
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_board_candles_from_beginning(session: Session) -> None:
    data = requests.get_board_candles(session, "MTSS", interval=10, end="2011-12-22")
    assert isinstance(data, list)
    assert len(data) > 500
    df = pd.DataFrame(data)
    assert df.columns.size == 7
    assert df.loc[0, "open"] == pytest.approx(202.7)
    assert df.loc[1, "close"] == pytest.approx(204.12)
    assert df.loc[2, "high"] == pytest.approx(205)
    assert df.loc[3, "low"] == pytest.approx(204.93)
    assert df.loc[4, "value"] == pytest.approx(3_990_683.9)
    assert df.loc[6, "begin"] == "2011-12-08 11:00:00"


def test_get_board_candles_to_end(session: Session) -> None:
    data = requests.get_board_candles(session, "TTLK", interval=31, start="2014-07-01")
    assert isinstance(data, list)
    assert len(data) > 52
    df = pd.DataFrame(data)
    assert df.columns.size == 7
    assert df.loc[0, "open"] == pytest.approx(0.152)
    assert df.loc[1, "close"] == pytest.approx(0.15689)
    assert df.loc[2, "high"] == pytest.approx(0.15998)
    assert df.loc[3, "low"] == pytest.approx(0.149)
    assert df.loc[4, "value"] == pytest.approx(2_713_625)
    assert df.loc[6, "begin"] == "2015-01-01 00:00:00"


def test_get_board_dates(session: Session) -> None:
    data = requests.get_board_dates(session)
    assert isinstance(data, list)
    assert len(data) == 1
    assert isinstance(data[0]["from"], str)
    assert isinstance(data[0]["till"], str)
    assert len(data[0]["from"]) == 10
    assert len(data[0]["till"]) == 10


def test_get_board_securities(session: Session) -> None:
    data = requests.get_board_securities(session)
    assert isinstance(data, list)
    assert len(data) > 200
    df = pd.DataFrame(data)
    df = df.set_index("SECID")
    assert df.loc["AKRN", "SHORTNAME"] == "Акрон"
    assert df.loc["GAZP", "REGNUMBER"] == "1-02-00028-A"
    assert df.loc["TTLK", "LOTSIZE"] == 1000
    assert df.loc["MRSB", "SHORTNAME"] == "МордЭнСб"
    assert df.loc["MRSB", "REGNUMBER"] == "1-01-55055-E"
    assert df.loc["MRSB", "LOTSIZE"] == 10000


def test_get_market_history_from_beginning(session: Session) -> None:
    data = requests.get_market_history(session, "AKRN", end="2006-12-01")
    assert isinstance(data, list)
    assert data[0]["TRADEDATE"] == "2006-10-11"
    assert data[-1]["TRADEDATE"] == "2006-12-01"
    assert len(data[-2]) == 5
    assert "CLOSE" in data[2]
    assert "VOLUME" in data[3]


def test_get_market_history_to_end(session: Session) -> None:
    data = requests.get_market_history(session, "MOEX", start="2017-10-02")
    assert isinstance(data, list)
    assert len(data) > 100
    assert data[0]["TRADEDATE"] == "2017-10-02"
    last_date = data[-1]["TRADEDATE"]
    assert isinstance(last_date, str)
    assert last_date >= "2018-11-19"


def test_get_board_history_from_beginning(session: Session) -> None:
    data = requests.get_board_history(session, "LSNGP", end="2014-08-01")
    df = pd.DataFrame(data)
    df = df.set_index("TRADEDATE")
    assert len(df.columns) == 4
    assert df.index[0] == "2014-06-09"
    assert df.loc["2014-06-09", "CLOSE"] == pytest.approx(14.7)
    assert df.loc["2014-08-01", "VOLUME"] == 4000


def test_get_board_history_to_end(session: Session) -> None:
    data = requests.get_board_history(session, "LSRG", start="2018-08-07")
    df = pd.DataFrame(data)
    df = df.set_index("TRADEDATE")
    assert len(df.columns) == 4
    assert df.index[0] == "2018-08-07"
    assert df.index[-1] >= "2018-11-19"
    assert df.loc["2018-08-07", "CLOSE"] == 777
    assert df.loc["2018-08-10", "VOLUME"] == 11313
    assert df.loc["2018-08-10", "BOARDID"] == "TQBR"
    assert df.loc["2018-08-10", "VALUE"] == pytest.approx(8_626_464.5)
    assert df.loc["2018-09-06", "CLOSE"] == pytest.approx(660)
    assert df.loc["2018-08-28", "VOLUME"] == 47428


def test_get_index_tickers(session: Session) -> None:
    data = requests.get_index_tickers(session, index="IMOEX", date="2023-03-03")
    assert len(data) == 40
    assert data[15]["ticker"] == "MAGN"
    assert data[25]["till"] == "2023-03-03"
    assert data[35]["tradingsession"] == 3


def test_get_engines(session: Session) -> None:
    data = requests.get_engines(session)
    assert isinstance(data, list)
    assert len(data) >= 10
    df = pd.DataFrame(data).set_index("name")
    assert df.loc["stock", "id"] == 1
    assert df.loc["stock", "title"] == "Фондовый рынок и рынок депозитов"
    assert "futures" in df.index


def test_get_engine_dailytable(session: Session) -> None:
    # по умолчанию dailytable — календарь исключений (выходные/праздники/переносы)
    data = requests.get_engine(session, "stock")
    assert isinstance(data, list)
    assert len(data) > 0
    row = data[0]
    assert {"date", "is_work_day", "start_time", "stop_time"} <= set(row)
    df = pd.DataFrame(data).set_index("date")
    # стабильные исторические записи (новый праздник в таблицу не задним числом)
    assert df.loc["2018-05-09", "is_work_day"] == 0  # перенос/праздник — нерабочий
    assert df.loc["2021-02-20", "is_work_day"] == 1  # суббота-отработка — рабочий


def test_get_engine_timetable(session: Session) -> None:
    data = requests.get_engine(session, "stock", "timetable")
    assert isinstance(data, list)
    assert len(data) == 7  # 7 дней недели
    df = pd.DataFrame(data).set_index("week_day")
    assert set(df.columns) >= {"is_work_day", "start_time", "stop_time"}


def test_get_engine_description(session: Session) -> None:
    data = requests.get_engine(session, "stock", "engine")
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["NAME"] == "stock"
