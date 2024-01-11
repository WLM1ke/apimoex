"""Клиент для MOEX ISS."""
from collections import abc
from typing import cast

import requests

Values = str | int | float
TableRow = dict[str, Values]
Table = list[TableRow]
TablesDict = dict[str, Table]
WebQuery = dict[str, str | int]

BASE_QUERY = {"iss.json": "extended", "iss.meta": "off"}


class ISSMoexError(Exception):
    """Базовое исключение."""


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
                    raise ISSMoexError(
                        f"Некорректные данные history.cursor {data['history.cursor']} для начальной позиции {start}"
                    )
                del data["history.cursor"]
                yield data
                start += cast(int, cursor["PAGESIZE"])
                if start >= cast(int, cursor["TOTAL"]):
                    return
            else:
                # Наименование ключа может быть любым
                key = next(iter(data))
                block_size = len(data[key])
                yield data
                if not block_size:
                    return
                start += block_size

    def get(self, start: int | None = None) -> dict[str, list[dict[str, str | int | float]]]:
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
                raise ISSMoexError("Неверный url", respond.url) from err
            else:
                _, data, *wrong_data = respond.json()
        if len(wrong_data) != 0:
            raise ISSMoexError("Ответ содержит некорректные данные", respond.url)
        return data

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
            # noinspection PyUnresolvedReferences
            for key, value in data.items():
                all_data.setdefault(key, []).extend(value)

        return all_data
