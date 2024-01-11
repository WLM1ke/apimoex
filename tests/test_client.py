import typing

import pytest
import requests

from apimoex import client


@pytest.fixture(scope="module", name="session")
def make_session():
    with requests.Session() as session:
        yield session


def test_iss_client_iterable():
    assert issubclass(client.ISSClient, typing.Iterable)


def test_repr(session):
    iss = client.ISSClient(session, "test_url", dict(a="b"))
    assert str(iss) == "ISSClient(url=test_url, query={'a': 'b'})"


def test_get(session):
    url = "https://iss.moex.com/iss/securities.json"
    query = dict(q="1-02-65104-D")
    iss = client.ISSClient(session, url, query)
    raw = iss.get()
    assert isinstance(raw, dict)
    assert len(raw) == 1
    data = raw["securities"]
    assert isinstance(data, list)
    assert len(data) == 4
    assert isinstance(data[0], dict)
    assert data[1]["regnumber"] == "1-02-65104-D"


def test_get_with_start(session):
    url = "https://iss.moex.com/iss/securities.json"
    query = dict(q="1-02-65104-D")
    iss = client.ISSClient(session, url, query)
    raw = iss.get(1)
    assert isinstance(raw, dict)
    assert len(raw) == 1
    data = raw["securities"]
    assert isinstance(data, list)
    assert len(data) == 3
    assert isinstance(data[0], dict)
    assert data[1]["regnumber"] == "1-02-65104-D"


def test_get_wrong_url(session):
    url = "https://iss.moex.com/iss/securities1.json"
    iss = client.ISSClient(session, url)
    with pytest.raises(client.ISSMoexError) as error:
        iss.get()
    assert "Неверный url" in str(error.value)
    assert "https://iss.moex.com/iss/securities1.json?iss.json=extended&iss.meta=off" in str(error.value)


def test_get_wrong_json(monkeypatch, session):
    url = "https://iss.moex.com/iss/securities.json"
    iss = client.ISSClient(session, url)
    # noinspection PyProtectedMember
    monkeypatch.setattr(requests.Response, "json", lambda x: [0, 1, 2])
    with pytest.raises(client.ISSMoexError) as error:
        iss.get()
    assert "Ответ содержит некорректные данные" in str(error.value)
    assert "https://iss.moex.com/iss/securities.json?iss.json=extended&iss.meta=off" in str(error.value)


def test_make_query_empty(session):
    iss = client.ISSClient(session, "test_url")
    # noinspection PyProtectedMember
    query = iss._make_query()
    assert isinstance(query, dict)
    assert len(query) == 2
    assert query["iss.json"] == "extended"
    assert query["iss.meta"] == "off"


def test_make_query_not_empty(session):
    iss = client.ISSClient(session, "test_url", dict(test_param="test_value"))
    # noinspection PyProtectedMember
    query = iss._make_query()
    assert isinstance(query, dict)
    assert len(query) == 3
    assert query["iss.json"] == "extended"
    assert query["iss.meta"] == "off"
    assert query["test_param"] == "test_value"


def test_make_query_not_empty_with_start(session):
    iss = client.ISSClient(session, "test_url", dict(test_param="test_value"))
    # noinspection PyProtectedMember
    query = iss._make_query(704)
    assert isinstance(query, dict)
    assert len(query) == 4
    assert query["iss.json"] == "extended"
    assert query["iss.meta"] == "off"
    assert query["test_param"] == "test_value"
    assert query["start"] == 704


def test_get_all_with_cursor(session):
    url = "https://iss.moex.com/iss/history/engines/stock/markets/shares/securities/SNGSP.json"
    query = {"from": "2018-01-01", "till": "2018-03-01"}
    iss = client.ISSClient(session, url, query)
    raw = iss.get_all()
    assert isinstance(raw, dict)
    assert len(raw) == 1
    data = raw["history"]
    assert isinstance(data, list)
    assert len(data) > 100
    assert data[0]["TRADEDATE"] == "2018-01-03"
    assert data[-1]["TRADEDATE"] == "2018-03-01"
    for row in data:
        for column in ["TRADEDATE", "OPEN", "LOW", "HIGH", "CLOSE", "VOLUME"]:
            assert column in row


def test_get_all_without_cursor(session):
    url = "https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/SNGSP.json"
    query = {"from": "2018-01-03", "till": "2018-06-01"}
    iss = client.ISSClient(session, url, query)
    raw = iss.get_all()
    assert isinstance(raw, dict)
    assert len(raw) == 1
    data = raw["history"]
    assert isinstance(data, list)
    assert len(data) > 100
    assert data[0]["TRADEDATE"] == "2018-01-03"
    assert data[-1]["TRADEDATE"] == "2018-06-01"
    for row in data:
        for column in ["TRADEDATE", "OPEN", "LOW", "HIGH", "CLOSE", "VOLUME"]:
            assert column in row


def test_wrong_cursor_size(monkeypatch, session):
    iss = client.ISSClient(session, "")
    fake_cursor = {"history.cursor": [0, 1]}

    monkeypatch.setattr(iss, "get", lambda x: fake_cursor)
    with pytest.raises(client.ISSMoexError) as error:
        iss.get_all()
    assert f"Некорректные данные history.cursor [0, 1] для начальной позиции 0" in str(error.value)


def test_wrong_cursor_index(monkeypatch, session):
    iss = client.ISSClient(session, "")
    fake_cursor = {"history.cursor": [{"INDEX": 1}]}

    monkeypatch.setattr(iss, "get", lambda x: fake_cursor)
    with pytest.raises(client.ISSMoexError) as error:
        iss.get_all()
    assert "Некорректные данные history.cursor [{'INDEX': 1}] для начальной позиции 0" in str(error.value)
