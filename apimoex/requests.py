"""Реализация части запросов к MOEX ISS.

При необходимости могут быть дополнены:
    Полный перечень запросов https://iss.moex.com/iss/reference/
    Дополнительное описание https://fs.moex.com/files/6523
"""

from typing import TYPE_CHECKING

from apimoex import client

if TYPE_CHECKING:
    import requests

__all__ = [
    "find_securities",
    "find_security_description",
    "get_board_candle_borders",
    "get_board_candles",
    "get_board_dates",
    "get_board_history",
    "get_board_securities",
    "get_engine",
    "get_engines",
    "get_index_tickers",
    "get_market_candle_borders",
    "get_market_candles",
    "get_market_history",
    "get_reference",
]


def _make_query(
    *,
    q: str | None = None,
    interval: int | None = None,
    start: str | None = None,
    end: str | None = None,
    date: str | None = None,
    table: str | None = None,
    columns: tuple[str, ...] | None = None,
) -> client.WebQuery:
    """Формирует дополнительные параметры запроса к MOEX ISS.

    В случае None значений не добавляются в запрос.

    :param q:
        Строка с частью характеристик бумаги для поиска.
    :param interval:
        Размер свечки.
    :param start:
        Начальная дата котировок.
    :param end:
        Конечная дата котировок.
    :param date:
        Точная дата (используется при получении тикеров в индексе).
    :param table:
        Таблица, которую нужно загрузить (для запросов, предполагающих наличие нескольких таблиц).
    :param columns:
        Кортеж столбцов, которые нужно загрузить.

    :return:
        Словарь с дополнительными параметрами запроса.
    """
    query: client.WebQuery = {}
    if q:
        query["q"] = q
    if interval:
        query["interval"] = interval
    if start:
        query["from"] = start
    if end:
        query["till"] = end
    if date:
        query["date"] = date
    if table:
        query["iss.only"] = f"{table},history.cursor"
    if columns:
        query[f"{table}.columns"] = ",".join(columns)

    return query


def _get_table(data: client.TablesDict, table: str) -> client.Table:
    """Извлекает конкретную таблицу из данных."""
    try:
        return data[table]
    except KeyError as err:
        raise client.ISSMoexError(f"Отсутствует таблица {table} в данных") from err


def _get_short_data(
    session: requests.Session,
    url: str,
    table: str,
    query: client.WebQuery | None = None,
) -> client.Table:
    """Получить данные для запроса с выдачей всей информации за раз.

    :param session:
        Сессия интернет соединения.
    :param url:
        URL запроса.
    :param table:
        Таблица, которую нужно выбрать.
    :param query:
        Дополнительные параметры запроса.

    :return:
        Конкретная таблица из запроса.
    """
    iss = client.ISSClient(session, url, query)
    data = iss.get()

    return _get_table(data, table)


def _get_long_data(
    session: requests.Session,
    url: str,
    table: str,
    query: client.WebQuery | None = None,
) -> client.Table:
    """Получить данные для запроса, в котором информация выдается несколькими блоками.

    :param session:
        Сессия интернет соединения.
    :param url:
        URL запроса.
    :param table:
        Таблица, которую нужно выбрать.
    :param query:
        Дополнительные параметры запроса.

    :return:
        Конкретная таблица из запроса.
    """
    iss = client.ISSClient(session, url, query)
    data = iss.get_all()

    return _get_table(data, table)


def get_reference(session: requests.Session, placeholder: str = "boards") -> list[dict[str, str | int | float]]:
    """Получить перечень доступных значений плейсхолдера в адресе запроса.

    Например в описание запроса https://iss.moex.com/iss/reference/32 присутствует следующий адрес
    /iss/engines/[engine]/markets/[market]/boards/[board]/securities с плейсхолдерами engines, markets и boards.

    Описание запроса - https://iss.moex.com/iss/reference/28

    :param session:
        Сессия интернет соединения.
    :param placeholder:
        Наименование плейсхолдера в адресе запроса: engines, markets, boards, boardgroups, durations, securitytypes,
        securitygroups, securitycollections

    :return:
        Список словарей, которые напрямую конвертируется в pandas.DataFrame.
    """
    url = "https://iss.moex.com/iss/index.json"

    return _get_short_data(session, url, placeholder)


def find_securities(
    session: requests.Session,
    string: str,
    columns: tuple[str, ...] | None = ("secid", "regnumber"),
) -> client.Table:
    """Найти инструменты по части Кода, Названию, ISIN, Идентификатору Эмитента, Номеру гос.регистрации.

    Один из вариантов использования - по регистрационному номеру узнать предыдущие тикеры эмитента, и с помощью
    нескольких запросов об истории котировок собрать длинную историю с использованием всех предыдущих тикеров.

    Описание запроса - https://iss.moex.com/iss/reference/5

    :param session:
        Сессия интернет соединения.
    :param string:
        Часть Кода, Названия, ISIN, Идентификатора Эмитента, Номера гос.регистрации.
    :param columns:
        Кортеж столбцов, которые нужно загрузить - по умолчанию тикер и номер государственно регистрации.
        Если пустой или None, то загружаются все столбцы.

    :return:
        Список словарей, которые напрямую конвертируется в pandas.DataFrame.
    """
    url = "https://iss.moex.com/iss/securities.json"
    table = "securities"
    query = _make_query(q=string, table=table, columns=columns)

    return _get_short_data(session, url, table, query)


def find_security_description(
    session: requests.Session,
    security: str,
    columns: tuple[str, ...] | None = ("name", "title", "value"),
) -> client.Table:
    """Получить спецификацию инструмента.

    Один из вариантов использования - по тикеру узнать дату начала торгов.

    Описание запроса - https://iss.moex.com/iss/reference/13

    :param session:
        Сессия интернет соединения.
    :param security:
        Тикер ценной бумаги.
    :param columns:
        Кортеж столбцов, которые нужно загрузить - по умолчанию краткое название, длинное название на русском и значение
        показателя.

    :return:
        Список словарей, которые напрямую конвертируется в pandas.DataFrame.
    """
    url = f"https://iss.moex.com/iss/securities/{security}.json"
    table = "description"
    query = _make_query(table=table, columns=columns)

    return _get_short_data(session, url, table, query)


def get_market_candle_borders(
    session: requests.Session,
    security: str,
    market: str = "shares",
    engine: str = "stock",
) -> client.Table:
    """Получить таблицу интервалов доступных дат для свечей различного размера на рынке для всех режимов торгов.

    Описание запроса - https://iss.moex.com/iss/reference/156

    :param session:
        Сессия интернет соединения.
    :param security:
        Тикер ценной бумаги.
    :param market:
        Рынок - по умолчанию акции.
    :param engine:
        Движок - по умолчанию акции.

    :return:
        Список словарей, которые напрямую конвертируется в pandas.DataFrame.
    """
    url = f"https://iss.moex.com/iss/engines/{engine}/markets/{market}/securities/{security}/candleborders.json"
    table = "borders"

    return _get_short_data(session, url, table)


def get_board_candle_borders(
    session: requests.Session,
    security: str,
    board: str = "TQBR",
    market: str = "shares",
    engine: str = "stock",
) -> client.Table:
    """Получить таблицу интервалов доступных дат для свечей различного размера в указанном режиме торгов.

    Описание запроса - https://iss.moex.com/iss/reference/48

    :param session:
        Сессия интернет соединения.
    :param security:
        Тикер ценной бумаги.
    :param board:
        Режим торгов - по умолчанию основной режим торгов T+2.
    :param market:
        Рынок - по умолчанию акции.
    :param engine:
        Движок - по умолчанию акции.

    :return:
        Список словарей, которые напрямую конвертируется в pandas.DataFrame.
    """
    url = (
        f"https://iss.moex.com/iss/engines/{engine}/markets/{market}/"
        f"boards/{board}/securities/{security}/candleborders.json"
    )
    table = "borders"

    return _get_short_data(session, url, table)


def get_market_candles(
    session: requests.Session,
    security: str,
    interval: int = 24,
    start: str | None = None,
    end: str | None = None,
    columns: tuple[str, ...] | None = (
        "begin",
        "open",
        "close",
        "high",
        "low",
        "value",
        "volume",
    ),
    market: str = "shares",
    engine: str = "stock",
) -> client.Table:
    """Получить свечи в формате HLOCV указанного инструмента на рынке для основного режима торгов за интервал дат.

    Если торговля идет в нескольких основных режимах, то на один интервал времени может быть выдано несколько свечек -
    по свечке на каждый режим. Предположительно такая ситуация может произойти для свечек длиннее 1 дня в периоды, когда
    менялся режим торгов.

    Описание запроса - https://iss.moex.com/iss/reference/155

    :param session:
        Сессия интернет соединения.
    :param security:
        Тикер ценной бумаги.
    :param interval:
        Размер свечки - целое число 1 (1 минута), 10 (10 минут), 60 (1 час), 24 (1 день), 7 (1 неделя), 31 (1 месяц) или
        4 (1 квартал). По умолчанию дневные данные.
    :param start:
        Дата вида ГГГГ-ММ-ДД. При отсутствии данные будут загружены с начала истории.
    :param end:
        Дата вида ГГГГ-ММ-ДД. При отсутствии данные будут загружены до конца истории. Для текущего дня будут
        загружены не окончательные данные, если торги продолжаются.
    :param columns:
        Кортеж столбцов, которые нужно загрузить - по умолчанию момент начала свечки и HLOCV. Если пустой или None, то
        загружаются все столбцы.
    :param market:
        Рынок - по умолчанию акции.
    :param engine:
        Движок - по умолчанию акции.

    :return:
        Список словарей, которые напрямую конвертируется в pandas.DataFrame.
    """
    url = f"https://iss.moex.com/iss/engines/{engine}/markets/{market}/securities/{security}/candles.json"
    table = "candles"
    query = _make_query(interval=interval, start=start, end=end, table=table, columns=columns)

    return _get_long_data(session, url, table, query)


def get_board_candles(
    session: requests.Session,
    security: str,
    interval: int = 24,
    start: str | None = None,
    end: str | None = None,
    columns: tuple[str, ...] | None = (
        "begin",
        "open",
        "close",
        "high",
        "low",
        "value",
        "volume",
    ),
    board: str = "TQBR",
    market: str = "shares",
    engine: str = "stock",
) -> client.Table:
    """Получить свечи в формате HLOCV указанного инструмента в указанном режиме торгов за интервал дат.

    Описание запроса - https://iss.moex.com/iss/reference/46

    :param session:
        Сессия интернет соединения.
    :param security:
        Тикер ценной бумаги.
    :param interval:
        Размер свечки - целое число 1 (1 минута), 10 (10 минут), 60 (1 час), 24 (1 день), 7 (1 неделя), 31 (1 месяц) или
        4 (1 квартал). По умолчанию дневные данные.
    :param start:
        Дата вида ГГГГ-ММ-ДД. При отсутствии данные будут загружены с начала истории.
    :param end:
        Дата вида ГГГГ-ММ-ДД. При отсутствии данные будут загружены до конца истории. Для текущего дня будут
        загружены не окончательные данные, если торги продолжаются.
    :param columns:
        Кортеж столбцов, которые нужно загрузить - по умолчанию момент начала свечки и HLOCV. Если пустой или None, то
        загружаются все столбцы.
    :param board:
        Режим торгов - по умолчанию основной режим торгов T+2.
    :param market:
        Рынок - по умолчанию акции.
    :param engine:
        Движок - по умолчанию акции.

    :return:
        Список словарей, которые напрямую конвертируется в pandas.DataFrame.
    """
    url = (
        f"https://iss.moex.com/iss/engines/{engine}/markets/{market}/boards/{board}/securities/{security}/candles.json"
    )
    table = "candles"
    query = _make_query(interval=interval, start=start, end=end, table=table, columns=columns)

    return _get_long_data(session, url, table, query)


def get_board_dates(
    session: requests.Session,
    board: str = "TQBR",
    market: str = "shares",
    engine: str = "stock",
) -> client.Table:
    """Получить интервал дат, доступных в истории для рынка по заданному режиму торгов.

    Описание запроса - https://iss.moex.com/iss/reference/26

    :param session:
        Сессия интернет соединения.
    :param board:
        Режим торгов - по умолчанию основной режим торгов T+2.
    :param market:
        Рынок - по умолчанию акции.
    :param engine:
        Движок - по умолчанию акции.

    :return:
        Список из одного элемента - словаря с ключами 'from' и 'till'.
    """
    url = f"https://iss.moex.com/iss/history/engines/{engine}/markets/{market}/boards/{board}/dates.json"
    table = "dates"

    return _get_short_data(session, url, table)


def get_board_securities(
    session: requests.Session,
    table: str = "securities",
    columns: tuple[str, ...] | None = ("SECID", "REGNUMBER", "LOTSIZE", "SHORTNAME"),
    board: str = "TQBR",
    market: str = "shares",
    engine: str = "stock",
) -> client.Table:
    """Получить таблицу инструментов по режиму торгов со вспомогательной информацией.

    Описание запроса - https://iss.moex.com/iss/reference/32

    :param session:
        Сессия интернет соединения.
    :param table:
        Таблица с данными, которую нужно вернуть: securities - справочник торгуемых ценных бумаг, marketdata -
        данные с результатами торгов текущего дня.
    :param columns:
        Кортеж столбцов, которые нужно загрузить - по умолчанию тикер, номер государственно регистрации,
        размер лота и краткое название. Если пустой или None, то загружаются все столбцы.
    :param board:
        Режим торгов - по умолчанию основной режим торгов T+2.
    :param market:
        Рынок - по умолчанию акции.
    :param engine:
        Движок - по умолчанию акции.

    :return:
        Список словарей, которые напрямую конвертируется в pandas.DataFrame.
    """
    url = f"https://iss.moex.com/iss/engines/{engine}/markets/{market}/boards/{board}/securities.json"
    query = _make_query(table=table, columns=columns)

    return _get_short_data(session, url, table, query)


def get_market_history(
    session: requests.Session,
    security: str,
    start: str | None = None,
    end: str | None = None,
    columns: tuple[str, ...] | None = (
        "BOARDID",
        "TRADEDATE",
        "CLOSE",
        "VOLUME",
        "VALUE",
    ),
    market: str = "shares",
    engine: str = "stock",
) -> client.Table:
    """Получить историю по одной бумаге на рынке для всех режимов торгов за интервал дат.

    На одну дату может приходиться несколько значений, если торги шли в нескольких режимах.

    Описание запроса - https://iss.moex.com/iss/reference/63

    :param session:
        Сессия интернет соединения.
    :param security:
        Тикер ценной бумаги.
    :param start:
        Дата вида ГГГГ-ММ-ДД. При отсутствии данные будут загружены с начала истории.
    :param end:
        Дата вида ГГГГ-ММ-ДД. При отсутствии данные будут загружены до конца истории.
    :param columns:
        Кортеж столбцов, которые нужно загрузить - по умолчанию режим торгов, дата торгов, цена закрытия и объем в
        штуках и стоимости. Если пустой или None, то загружаются все столбцы.
    :param market:
        Рынок - по умолчанию акции.
    :param engine:
        Движок - по умолчанию акции.

    :return:
        Список словарей, которые напрямую конвертируется в pandas.DataFrame.
    """
    url = f"https://iss.moex.com/iss/history/engines/{engine}/markets/{market}/securities/{security}.json"
    table = "history"
    query = _make_query(start=start, end=end, table=table, columns=columns)

    return _get_long_data(session, url, table, query)


def get_board_history(
    session: requests.Session,
    security: str,
    start: str | None = None,
    end: str | None = None,
    columns: tuple[str, ...] | None = (
        "BOARDID",
        "TRADEDATE",
        "CLOSE",
        "VOLUME",
        "VALUE",
    ),
    board: str = "TQBR",
    market: str = "shares",
    engine: str = "stock",
) -> client.Table:
    """Получить историю торгов для указанной бумаги в указанном режиме торгов за указанный интервал дат.

    Описание запроса - https://iss.moex.com/iss/reference/65

    :param session:
        Сессия интернет соединения.
    :param security:
        Тикер ценной бумаги.
    :param start:
        Дата вида ГГГГ-ММ-ДД. При отсутствии данные будут загружены с начала истории.
    :param end:
        Дата вида ГГГГ-ММ-ДД. При отсутствии данные будут загружены до конца истории.
    :param columns:
        Кортеж столбцов, которые нужно загрузить - по умолчанию режим торгов, дата торгов, цена закрытия и объем в
        штуках и стоимости. Если пустой или None, то загружаются все столбцы.
    :param board:
        Режим торгов - по умолчанию основной режим торгов T+2.
    :param market:
        Рынок - по умолчанию акции.
    :param engine:
        Движок - по умолчанию акции.

    :return:
        Список словарей, которые напрямую конвертируется в pandas.DataFrame.
    """
    url = (
        f"https://iss.moex.com/iss/history/engines/{engine}/markets/{market}/boards/{board}/securities/{security}.json"
    )
    table = "history"
    query = _make_query(start=start, end=end, table=table, columns=columns)

    return _get_long_data(session, url, table, query)


def get_index_tickers(
    session: requests.Session,
    index: str,
    date: str | None = None,
    columns: tuple[str, ...] | None = (
        "ticker",
        "from",
        "till",
        "tradingsession",
    ),
    market: str = "index",
    engine: str = "stock",
) -> client.Table:
    """Получить информацию по составу указанного индекса за указанную дату.

    Описание запроса - https://iss.moex.com/iss/reference/148

    Список индексов - https://iss.moex.com/iss/statistics/engines/stock/markets/index/analytics

    :param session:
        Сессия интернет соединения.
    :param index:
        Название индекса. Например, IMOEX.
    :param date:
        Дата вида ГГГГ-ММ-ДД. Если указано, то будут показаны только активные инструменты,
        по которым тогда рассчитывалось значение индекса. Если в указанный день не было торгов, то вернёт пустой список!
        При отсутствии данные будут загружены с начала истории.
    :param columns:
        Кортеж столбцов, которые нужно загрузить - по умолчанию режим торгов, дата торгов, цена закрытия и объем в
        штуках и стоимости. Если пустой или None, то загружаются все столбцы.
    :param market:
        Рынок - по умолчанию индексы.
    :param engine:
        Движок - по умолчанию акции.

    :return:
        Список словарей, которые напрямую конвертируется в pandas.DataFrame.
    """
    url = f"https://iss.moex.com/iss/statistics/engines/{engine}/markets/{market}/analytics/{index}/tickers.json"
    table = "tickers"
    query = _make_query(date=date, table=table, columns=columns)

    return _get_short_data(session, url, table, query)


def get_engines(session: requests.Session) -> client.Table:
    """Получить перечень доступных торговых систем (движков) MOEX.

    Например: https://iss.moex.com/iss/engines.json — stock, futures, currency и т.д.

    Описание запроса - https://iss.moex.com/iss/reference/391

    :param session:
        Сессия интернет соединения.

    :return:
        Список словарей (id, name, title), который напрямую конвертируется в pandas.DataFrame.
    """
    url = "https://iss.moex.com/iss/engines.json"
    table = "engines"

    return _get_short_data(session, url, table)


def get_engine(
    session: requests.Session,
    engine: str = "stock",
    table: str = "dailytable",
) -> client.Table:
    """Получить описание и режим работы торговой системы (движка).

    Например: https://iss.moex.com/iss/engines/stock.json — содержит три таблицы:
      * ``engine``     — описание движка (NAME, title, short_title);
      * ``timetable``  — недельное расписание (week_day, is_work_day, start/stop_time);
      * ``dailytable`` — календарь исключений по датам (date, is_work_day, start/stop_time):
        ``is_work_day=0`` — выходной/праздник, ``1`` — перенос рабочего дня. Источник
        торгового календаря MOEX (выходные/праздники/переносы).

    Описание запроса - https://iss.moex.com/iss/reference/397

    :param session:
        Сессия интернет соединения.
    :param engine:
        Движок - по умолчанию ``stock`` (фондовый рынок).
    :param table:
        Какую из таблиц вернуть: ``dailytable`` (по умолчанию, календарь),
        ``timetable`` (недельное расписание) или ``engine`` (описание).

    :return:
        Список словарей выбранной таблицы, который напрямую конвертируется в pandas.DataFrame.
    """
    url = f"https://iss.moex.com/iss/engines/{engine}.json"

    return _get_short_data(session, url, table)
