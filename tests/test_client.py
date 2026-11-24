"""Тесты клиента MOEX ISS."""

from collections import abc
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
import requests

from apimoex import client

if TYPE_CHECKING:
    from collections.abc import Iterator

    from apimoex.types import TablesDict, WebQuery

_CA_BUNDLE = Path(__file__).parent / "certs" / "russian_trusted_root_ca.pem"


@pytest.fixture(scope="module", name="session")
def make_session() -> Iterator[requests.Session]:
    with requests.Session() as session:
        session.verify = str(_CA_BUNDLE)
        yield session


def test_iss_client_iterable() -> None:
    assert issubclass(client.ISSClient, abc.Iterable)


def test_repr(session: requests.Session) -> None:
    query: WebQuery = {"a": "b"}
    iss = client.ISSClient(session, "test_url", query)
    assert str(iss) == "ISSClient(url=test_url, query={'a': 'b'})"


def test_get(session: requests.Session) -> None:
    url = "https://iss.moex.com/iss/securities.json"
    query: WebQuery = {"q": "1-02-65104-D"}
    iss = client.ISSClient(session, url, query)
    raw = iss.get()
    assert isinstance(raw, dict)
    assert len(raw) == 1
    data = raw["securities"]
    assert isinstance(data, list)
    assert len(data) == 4
    assert isinstance(data[0], dict)
    assert data[1]["regnumber"] == "1-02-65104-D"


def test_get_with_start(session: requests.Session) -> None:
    url = "https://iss.moex.com/iss/securities.json"
    query: WebQuery = {"q": "1-02-65104-D"}
    iss = client.ISSClient(session, url, query)
    raw = iss.get(1)
    assert isinstance(raw, dict)
    assert len(raw) == 1
    data = raw["securities"]
    assert isinstance(data, list)
    assert len(data) == 3
    assert isinstance(data[0], dict)
    assert data[1]["regnumber"] == "1-02-65104-D"


def test_get_wrong_url(session: requests.Session) -> None:
    url = "https://iss.moex.com/iss/securities1.json"
    iss = client.ISSClient(session, url)
    with pytest.raises(client.ISSHTTPError) as error:
        _ = iss.get()
    assert "Invalid URL" in str(error.value)
    assert "https://iss.moex.com/iss/securities1.json?iss.json=extended&iss.meta=off" in str(error.value)


def test_get_wrong_json(monkeypatch: pytest.MonkeyPatch, session: requests.Session) -> None:
    url = "https://iss.moex.com/iss/securities.json"
    iss = client.ISSClient(session, url)

    def fake_json(_response: requests.Response) -> object:
        return [0, 1, 2]

    monkeypatch.setattr(requests.Response, "json", fake_json)
    with pytest.raises(client.ISSResponseError) as error:
        _ = iss.get()
    assert "Response contains invalid data" in str(error.value)
    assert "https://iss.moex.com/iss/securities.json?iss.json=extended&iss.meta=off" in str(error.value)


def test_get_wrong_json_not_list(monkeypatch: pytest.MonkeyPatch, session: requests.Session) -> None:
    iss = client.ISSClient(session, "https://iss.moex.com/iss/securities.json")

    def fake_json(_response: requests.Response) -> object:
        return {"securities": []}

    monkeypatch.setattr(requests.Response, "json", fake_json)
    with pytest.raises(client.ISSResponseError) as error:
        _ = iss.get()
    assert "Response contains invalid data" in str(error.value)


def test_get_wrong_json_not_table(monkeypatch: pytest.MonkeyPatch, session: requests.Session) -> None:
    iss = client.ISSClient(session, "https://iss.moex.com/iss/securities.json")

    def fake_json(_response: requests.Response) -> object:
        return [dict[str, str](), "data"]

    monkeypatch.setattr(requests.Response, "json", fake_json)
    with pytest.raises(client.ISSResponseError) as error:
        _ = iss.get()
    assert "Response contains invalid data" in str(error.value)


def test_make_query_empty(session: requests.Session) -> None:
    iss = client.ISSClient(session, "test_url")
    query = iss._make_query()  # pyright: ignore[reportPrivateUsage]
    assert isinstance(query, dict)
    assert len(query) == 2
    assert query["iss.json"] == "extended"
    assert query["iss.meta"] == "off"


def test_make_query_not_empty(session: requests.Session) -> None:
    credentials: WebQuery = {"test_param": "test_value"}
    iss = client.ISSClient(session, "test_url", credentials)
    query = iss._make_query()  # pyright: ignore[reportPrivateUsage]
    assert isinstance(query, dict)
    assert len(query) == 3
    assert query["iss.json"] == "extended"
    assert query["iss.meta"] == "off"
    assert query["test_param"] == "test_value"


def test_make_query_not_empty_with_start(session: requests.Session) -> None:
    credentials: WebQuery = {"test_param": "test_value"}
    iss = client.ISSClient(session, "test_url", credentials)
    query = iss._make_query(704)  # pyright: ignore[reportPrivateUsage]
    assert isinstance(query, dict)
    assert len(query) == 4
    assert query["iss.json"] == "extended"
    assert query["iss.meta"] == "off"
    assert query["test_param"] == "test_value"
    assert query["start"] == 704


def test_get_all_with_cursor(session: requests.Session) -> None:
    url = "https://iss.moex.com/iss/history/engines/stock/markets/shares/securities/SNGSP.json"
    query: WebQuery = {"from": "2018-01-01", "till": "2018-03-01"}
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


def test_get_all_without_cursor(session: requests.Session) -> None:
    url = "https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/SNGSP.json"
    query: WebQuery = {"from": "2018-01-03", "till": "2018-06-01"}
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


def test_wrong_cursor_size(monkeypatch: pytest.MonkeyPatch, session: requests.Session) -> None:
    iss = client.ISSClient(session, "")

    def fake_get(_start: int | None = None) -> TablesDict:
        return cast("TablesDict", {"history.cursor": [0, 1]})

    monkeypatch.setattr(iss, "get", fake_get)
    with pytest.raises(client.ISSCursorError) as error:
        _ = iss.get_all()
    assert "Invalid history.cursor data [0, 1] for start position 0" in str(error.value)


def test_wrong_cursor_index(monkeypatch: pytest.MonkeyPatch, session: requests.Session) -> None:
    iss = client.ISSClient(session, "")

    def fake_get(_start: int | None = None) -> TablesDict:
        return {"history.cursor": [{"INDEX": 1}]}

    monkeypatch.setattr(iss, "get", fake_get)
    with pytest.raises(client.ISSCursorError) as error:
        _ = iss.get_all()
    assert "Invalid history.cursor data [{'INDEX': 1}] for start position 0" in str(error.value)
