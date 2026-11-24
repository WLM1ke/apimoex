"""Клиент для MOEX ISS."""

from collections import abc
from typing import Final, cast

import requests

from apimoex.types import Table, TablesDict, WebQuery

# Extended JSON always returns two blocks: the header and the data.
_RESPONSE_BLOCKS = 2

BASE_QUERY: Final = {"iss.json": "extended", "iss.meta": "off"}


class ISSMoexError(Exception):
    """Base exception."""


class ISSHTTPError(ISSMoexError):
    """The HTTP request to MOEX ISS failed."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Invalid URL: {url}")


class ISSResponseError(ISSMoexError):
    """The MOEX ISS response contains invalid data."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Response contains invalid data: {url}")


class ISSCursorError(ISSMoexError):
    """Invalid history.cursor data."""

    def __init__(self, cursor: Table, start: int) -> None:
        super().__init__(f"Invalid history.cursor data {cursor} for start position {start}")


class ISSTableNotFoundError(ISSMoexError):
    """The requested table is missing in the response."""

    def __init__(self, table: str) -> None:
        super().__init__(f"Table {table} is missing in the response")


class ISSClient(abc.Iterable[TablesDict]):
    """Клиент для MOEX ISS.

    Для работы клиента необходимо передать requests.Session.

    Загружает данные для простых ответов с помощью метода get. Для ответов состоящих из нескольких блоков данных
    поддерживается протокол итерируемого для отдельных блоков или метод get_all для их автоматического сбора.
    """

    def __init__(self, session: requests.Session, url: str, query: WebQuery | None = None) -> None:
        """MOEX ISS является REST сервером.

        Полный перечень запросов и параметров к ним https://iss.moex.com/iss/reference/
        Дополнительное описание https://fs.moex.com/files/6523

        :param session:
            Сессия интернет соединения.
        :param url:
            Адрес запроса.
        :param query:
            Перечень дополнительных параметров запроса. К списку дополнительных параметров всегда добавляется
            требование предоставить ответ в виде расширенного json без метаданных.
        """
        self._session = session
        self._url = url
        self._query = query or {}

    def __repr__(self) -> str:
        """Наименование класса и содержание запроса к ISS Moex."""
        return f"{self.__class__.__name__}(url={self._url}, query={self._query})"

    def __iter__(self) -> abc.Iterator[TablesDict]:
        """Генератор по ответам состоящим из нескольких блоков.

        На часть запросов выдается только начальный блок данных (обычно из 100 элементов). Генератор обеспечивает
        загрузку всех блоков. При этом в ответах на некоторые запросы может содержаться курсор с положением текущего
        блока данных (позволяет сэкономить один запрос). Генератор обеспечивает обработку ответов как с курсором, так и
        без него.

        Ответ представляет словарь, каждый из ключей которого отдельная таблица с данными. Таблица представлена в виде
        списка словарей, где каждый ключ словаря соответствует отдельному столбцу.
        """
        start = 0
        while True:
            data = self.get(start)
            if "history.cursor" in data:
                cursor, *wrong_data = data["history.cursor"]
                if len(wrong_data) != 0 or cursor["INDEX"] != start:
                    raise ISSCursorError(data["history.cursor"], start)
                del data["history.cursor"]
                yield data
                start += cast("int", cursor["PAGESIZE"])
                if start >= cast("int", cursor["TOTAL"]):
                    return
            else:
                # Наименование ключа может быть любым
                key = next(iter(data))
                block_size = len(data[key])
                yield data
                if not block_size:
                    return
                start += block_size

    def get(self, start: int | None = None) -> TablesDict:
        """Загрузка данных.

        :param start:
            Номер элемента с которого нужно загрузить данные. Используется для дозагрузки данных, состоящих из
            нескольких блоков. При отсутствии данные загружаются с начального элемента.
        :return:
            Блок данных с отброшенной вспомогательной информацией - словарь, каждый ключ которого
            соответствует одной из таблиц с данными. Таблицы являются списками словарей, которые напрямую конвертируются
            в pandas.DataFrame.
        """
        query = self._make_query(start)
        with self._session.get(self._url, params=query) as respond:
            try:
                respond.raise_for_status()
            except requests.HTTPError as err:
                raise ISSHTTPError(respond.url) from err
            response = cast("object", respond.json())
        if not isinstance(response, list):
            raise ISSResponseError(respond.url)
        blocks = cast("list[object]", response)
        if len(blocks) != _RESPONSE_BLOCKS:
            raise ISSResponseError(respond.url)
        _, data = blocks
        if not isinstance(data, dict):
            raise ISSResponseError(respond.url)
        return cast("TablesDict", data)

    def _make_query(self, start: int | None = None) -> WebQuery:
        """К общему набору параметров запроса добавляется требование предоставить ответ в виде расширенного json."""
        query: WebQuery = dict(**BASE_QUERY, **self._query)
        if start:
            query["start"] = start

        return query

    def get_all(self) -> TablesDict:
        """Собирает все блоки данных для запросов, ответы на которые выдаются по частям отдельными блоками.

        :return:
            Объединенные из всех блоков данные с отброшенной вспомогательной информацией - словарь, каждый ключ которого
            соответствует одной из таблиц с данными. Таблицы являются списками словарей, которые напрямую конвертируются
            в pandas.DataFrame.
        """
        all_data: TablesDict = {}
        for data in self:
            for key, value in data.items():
                all_data.setdefault(key, []).extend(value)

        return all_data
