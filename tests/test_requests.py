"""Тесты для разнообразных запросов."""
import pandas as pd
import pytest
from requests import Session

from apimoex import client
from apimoex import requests


@pytest.fixture(scope="module", name="session")
def make_session():
    """Создание http сессии."""
    with Session() as session:
        yield session


def test_make_query_empty():
    # noinspection PyProtectedMember
    query = requests._make_query()
    assert query == {}


def test_make_query_full():
    # noinspection PyProtectedMember
    query = requests._make_query(
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
    assert query["iss.only"] == f"new_table,history.cursor"
    assert query["new_table.columns"] == "4,a"


def test_get_table():
    # noinspection PyProtectedMember
    query = requests._get_table(
        dict(a="b"), "a"
    )
    assert query == "b"


def test_get_table_notable():
    with pytest.raises(client.ISSMoexError) as error:
        # noinspection PyProtectedMember
        requests._get_table(
            dict(a="b"), "b"
        )
    assert "Отсутствует таблица b в данных" in str(error.value)


def test_get_reference(session):
    data = requests.get_reference(session, "engines")
    assert isinstance(data, list)
    assert len(data) == 8
    assert data == [
        {"id": 1, "name": "stock", "title": "Фондовый рынок и рынок депозитов"},
        {"id": 2, "name": "state", "title": "Рынок ГЦБ (размещение)"},
        {"id": 3, "name": "currency", "title": "Валютный рынок"},
        {"id": 4, "name": "futures", "title": "Срочный рынок"},
        {"id": 5, "name": "commodity", "title": "Товарный рынок"},
        {"id": 6, "name": "interventions", "title": "Товарные интервенции"},
        {"id": 7, "name": "offboard", "title": "ОТС-система"},
        {'id': 9, 'name': 'agro', 'title': 'Агро'},
    ]


check_points = [
    ("1-02-65104-D", {"UPRO", "EONR", "OGK4"}),
    ("10301481B", {"SBER", "SBER03"}),
    ("20301481B", {"SBERP", "SBERP03"}),
    ("1-02-06556-A", {"PHOR"}),
]


@pytest.mark.parametrize("reg_number, expected", check_points)
def test_find_securities(session, reg_number, expected):
    data = requests.find_securities(session, reg_number)
    assert isinstance(data, list)
    assert expected == {row["secid"] for row in data if row["regnumber"] == reg_number}


def test_find_security_description(session):
    data = requests.find_security_description(session, "IRAO")
    print(data)
    assert isinstance(data, list)
    assert len(data) == 21
    assert data[8] == dict(name="ISSUEDATE", title="Дата начала торгов", value="2009-12-01")


def test_get_market_candle_borders(session):
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


def test_get_board_candle_borders(session):
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


def test_get_market_candles_from_beginning(session):
    data = requests.get_market_candles(session, "RTKM", interval=1, end="2011-12-16")
    assert isinstance(data, list)
    assert len(data) > 500
    df = pd.DataFrame(data)
    assert df.columns.size == 6
    assert df.loc[0, "open"] == pytest.approx(141.55)
    assert df.loc[1, "close"] == pytest.approx(141.59)
    assert df.loc[2, "high"] == pytest.approx(142.4)
    assert df.loc[3, "low"] == pytest.approx(140.81)
    assert df.loc[4, "value"] == pytest.approx(2_586_296.9)
    assert df.loc[6, "begin"] == "2011-12-15 10:06:00"


def test_get_market_candles_to_end(session):
    data = requests.get_market_candles(session, "LSRG", interval=4, start="2008-01-01")
    assert isinstance(data, list)
    assert len(data) > 47
    df = pd.DataFrame(data)
    assert df.columns.size == 6
    assert df.loc[0, "open"] == pytest.approx(1130)
    assert df.loc[1, "close"] == pytest.approx(970)
    assert df.loc[2, "high"] == pytest.approx(1045)
    assert df.loc[3, "low"] == pytest.approx(429.9)
    assert df.loc[4, "value"] == pytest.approx(1109833660.9)
    assert df.loc[6, "begin"] == "2012-07-01 00:00:00"


def test_get_market_candles_empty_history(session):
    data = requests.get_market_candles(session, "KSGR", interval=24)
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_board_candles_from_beginning(session):
    data = requests.get_board_candles(session, "MTSS", interval=10, end="2011-12-22")
    assert isinstance(data, list)
    assert len(data) > 500
    df = pd.DataFrame(data)
    assert df.columns.size == 6
    assert df.loc[0, "open"] == pytest.approx(202.7)
    assert df.loc[1, "close"] == pytest.approx(204.12)
    assert df.loc[2, "high"] == pytest.approx(205)
    assert df.loc[3, "low"] == pytest.approx(204.93)
    assert df.loc[4, "value"] == pytest.approx(3_990_683.9)
    assert df.loc[6, "begin"] == "2011-12-08 11:00:00"


def test_get_board_candles_to_end(session):
    data = requests.get_board_candles(session, "TTLK", interval=31, start="2014-07-01")
    assert isinstance(data, list)
    assert len(data) > 52
    df = pd.DataFrame(data)
    assert df.columns.size == 6
    assert df.loc[0, "open"] == pytest.approx(0.152)
    assert df.loc[1, "close"] == pytest.approx(0.15689)
    assert df.loc[2, "high"] == pytest.approx(0.15998)
    assert df.loc[3, "low"] == pytest.approx(0.149)
    assert df.loc[4, "value"] == pytest.approx(2_713_625)
    assert df.loc[6, "begin"] == "2015-01-01 00:00:00"


def test_get_board_dates(session):
    data = requests.get_board_dates(session)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['from'] == "1997-03-24"
    assert data[0]['till'] >= "2019-09-10"


def test_get_board_securities(session):
    data = requests.get_board_securities(session)
    assert isinstance(data, list)
    assert len(data) > 200
    df = pd.DataFrame(data)
    df.set_index("SECID", inplace=True)
    assert df.loc["AKRN", "SHORTNAME"] == "Акрон"
    assert df.loc["GAZP", "REGNUMBER"] == "1-02-00028-A"
    assert df.loc["TTLK", "LOTSIZE"] == 1000
    assert df.loc["MRSB", "SHORTNAME"] == "МордЭнСб"
    assert df.loc["MRSB", "REGNUMBER"] == "1-01-55055-E"
    assert df.loc["MRSB", "LOTSIZE"] == 10000
    assert df.index[0] == "ABRD"
    assert df["SHORTNAME"].iat[0] == "АбрауДюрсо"
    assert df["REGNUMBER"].iat[0] == "1-02-12500-A"
    assert df["LOTSIZE"].iat[0] == 10
    assert df["SHORTNAME"].iat[-1] == "ЗВЕЗДА ао"
    assert df["REGNUMBER"].iat[-1] == "1-01-00169-D"
    assert df["LOTSIZE"].iat[-1] == 1000
    assert df.index[-1] == "ZVEZ"


def test_get_market_history_from_beginning(session):
    data = requests.get_market_history(session, "AKRN", end="2006-12-01")
    assert isinstance(data, list)
    assert data[0]["TRADEDATE"] == "2006-10-11"
    assert data[-1]["TRADEDATE"] == "2006-12-01"
    assert len(data[-2]) == 5
    assert "CLOSE" in data[2]
    assert "VOLUME" in data[3]


def test_get_market_history_to_end(session):
    data = requests.get_market_history(session, "MOEX", start="2017-10-02")
    assert isinstance(data, list)
    assert len(data) > 100
    assert data[0]["TRADEDATE"] == "2017-10-02"
    assert data[-1]["TRADEDATE"] >= "2018-11-19"


def test_get_board_history_from_beginning(session):
    data = requests.get_board_history(session, "LSNGP", end="2014-08-01")
    df = pd.DataFrame(data)
    df.set_index("TRADEDATE", inplace=True)
    assert len(df.columns) == 4
    assert df.index[0] == "2014-06-09"
    assert df.at["2014-06-09", "CLOSE"] == pytest.approx(14.7)
    assert df.at["2014-08-01", "VOLUME"] == 4000


def test_get_board_history_to_end(session):
    data = requests.get_board_history(session, "LSRG", start="2018-08-07")
    df = pd.DataFrame(data)
    df.set_index("TRADEDATE", inplace=True)
    assert len(df.columns) == 4
    assert df.index[0] == "2018-08-07"
    assert df.index[-1] >= "2018-11-19"
    assert df.at["2018-08-07", "CLOSE"] == 777
    assert df.at["2018-08-10", "VOLUME"] == 11313
    assert df.at["2018-08-10", "BOARDID"] == "TQBR"
    assert df.at["2018-08-10", "VALUE"] == pytest.approx(8_626_464.5)
    assert df.at["2018-09-06", "CLOSE"] == pytest.approx(660)
    assert df.at["2018-08-28", "VOLUME"] == 47428
