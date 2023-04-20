Справочник API
==============

Функции-запросы
----------------

Справочная информация
^^^^^^^^^^^^^^^^^^^^^
Функции из данного раздела носят вспомогательный характер и нужны для получения данных для построения остальных
запросов.

.. autofunction:: apimoex.get_reference

.. autofunction:: apimoex.find_securities

.. autofunction:: apimoex.find_security_description

.. autofunction:: apimoex.get_index_tickers

Исторические данные по свечкам
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
MOEX ISS формирует свечки в формате HLOCV, при этом используются следующие условные числовые коды:

* 1 - 1 минута
* 10 - 10 минут
* 60 - 1 час
* 24 - 1 день
* 7 - 1 неделя
* 31 - 1 месяц
* 4 - 1 квартал

Для разных свечек и инструментов доступна информация за разные интервалы дат, уточнить которые можно с помощью функции
get_market_candle_borders() или get_board_candle_borders(), а получить исторические значения свечек с помощью
get_market_candles() или get_board_candles(), используя числовой код размера свечки.

.. autofunction:: apimoex.get_market_candle_borders

.. autofunction:: apimoex.get_board_candle_borders

.. autofunction:: apimoex.get_market_candles

.. autofunction:: apimoex.get_board_candles

Исторические данные по дневным котировкам
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
В отличие от свечек, функции данного раздела предоставляют много вспомогательной информации и имеют более глубокую историю.
Функция get_board_dates() позволяет проверить для каких дат имеются исторические котировки.
Функция get_board_securities() позволяет получить данные о размере лотов и прочей информации по всем торгуемым бумагам в
конкретном режиме торгов. Функции get_market_history() и get_board_history() позволяют запросить исторические дневные
котировки с различной вспомогательной информацией для конкретной бумаги для всех режимов торгов рынка или для
конкретного режима торгов, соответственно.

.. autofunction:: apimoex.get_board_dates

.. autofunction:: apimoex.get_board_securities

.. autofunction:: apimoex.get_market_history

.. autofunction:: apimoex.get_board_history

Реализация произвольного запроса
--------------------------------
Для осуществления запроса необходимо начать сессию соединений с MOEX ISS и передать клиенту корректный url и
дополнительные параметры:

* Полный перечень возможных `запросов <https://iss.moex.com/iss/reference/>`_ к MOEX ISS
* Официальное `Руководство разработчика <https://fs.moex.com/files/6523>`_ с дополнительной информацией

.. autoclass:: apimoex.ISSClient
    :members:
    :show-inheritance:
