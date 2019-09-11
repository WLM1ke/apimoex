MOEX ISS API
====================
.. image:: https://github.com/WLM1ke/apimoex/workflows/tests/badge.svg
    :target: https://github.com/WLM1ke/apimoex/actions
.. image:: https://codecov.io/gh/WLM1ke/apimoex/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/WLM1ke/apimoex
.. image:: https://badge.fury.io/py/apimoex.svg
    :target: https://badge.fury.io/py/apimoex

Реализация части  запросов к `MOEX Informational & Statistical Server <https://www.moex.com/a2193>`_.

Документация
------------
https://wlm1ke.github.io/apimoex/

Основные возможности
--------------------
Реализовано несколько функций-запросов информации о торгуемых акциях и их исторических котировках, результаты которых
напрямую конвертируются в pandas.DataFrame.

Работа функций базируется на универсальном клиенте, позволяющем осуществлять произвольные запросы к MOEX ISS, поэтому
перечень доступных функций-запросов может быть легко расширен. При необходимости добавления функций воспользуйтесь
`Issues <https://github.com/WLM1ke/apimoex/issues>`_ на GitHub с указанием ссылки на описание запроса:

* Полный перечень возможных `запросов <https://iss.moex.com/iss/reference/>`_ к MOEX ISS
* Официальное `Руководство разработчика <https://fs.moex.com/files/6523>`_ с дополнительной информацией

Начало работы
=============
Установка
---------

.. code-block:: Bash

   $ pip install apimoex

Пример использования реализованных запросов
-------------------------------------------
История котировок SNGSP в режиме TQBR::

   import requests

   import apimoex
   import pandas as pd


   with requests.Session() as session:
       data = apimoex.get_board_history(session, 'SNGSP')
       df = pd.DataFrame(data)
       df.set_index('TRADEDATE', inplace=True)
       print(df.head(), '\n')
       print(df.tail(), '\n')
       df.info()

.. code-block::

               BOARDID  CLOSE    VOLUME         VALUE
    TRADEDATE
    2014-06-09    TQBR  27.48  12674200  3.484352e+08
    2014-06-10    TQBR  27.55  14035900  3.856417e+08
    2014-06-11    TQBR  28.15  27208800  7.602146e+08
    2014-06-16    TQBR  28.27  68059900  1.913160e+09
    2014-06-17    TQBR  28.20  22101600  6.292844e+08

               BOARDID   CLOSE     VOLUME         VALUE
    TRADEDATE
    2019-09-04    TQBR  38.060  243010500  9.348435e+09
    2019-09-05    TQBR  36.140  129366600  4.704949e+09
    2019-09-06    TQBR  35.475   62389000  2.201887e+09
    2019-09-09    TQBR  34.570   54331300  1.905837e+09
    2019-09-10    TQBR  35.250   45966000  1.605849e+09

    <class 'pandas.core.frame.DataFrame'>
    Index: 1326 entries, 2014-06-09 to 2019-09-10
    Data columns (total 4 columns):
    BOARDID    1326 non-null object
    CLOSE      1326 non-null float64
    VOLUME     1326 non-null int64
    VALUE      1326 non-null float64
    dtypes: float64(2), int64(1), object(1)
    memory usage: 51.8+ KB

Пример реализации запроса с помощью клиента
-------------------------------------------
Перечень акций, торгующихся в режиме TQBR (`описание запроса <https://iss.moex.com/iss/reference/32>`_)::

   import requests

   import apimoex
   import pandas as pd


   request_url = ('https://iss.moex.com/iss/engines/stock/'
                  'markets/shares/boards/TQBR/securities.json')
   arguments = {'securities.columns': ('SECID,'
                                       'REGNUMBER,'
                                       'LOTSIZE,'
                                       'SHORTNAME')}
   with requests.Session() as session:
       iss = apimoex.ISSClient(session, request_url, arguments)
       data = iss.get()
       df = pd.DataFrame(data['securities'])
       df.set_index('SECID', inplace=True)
       print(df.head(), '\n')
       print(df.tail(), '\n')
       df.info()

.. code-block::

              REGNUMBER  LOTSIZE   SHORTNAME
    SECID
    ABRD   1-02-12500-A       10  АбрауДюрсо
    AFKS   1-05-01669-A      100  Система ао
    AFLT   1-01-00010-A       10    Аэрофлот
    AGRO           None        1    AGRO-гдр
    AKRN   1-03-00207-A        1       Акрон

              REGNUMBER  LOTSIZE   SHORTNAME
    SECID
    YNDX           None        1  Yandex clA
    YRSB   1-01-50099-A       10     ТНСэнЯр
    YRSBP  2-01-50099-A       10   ТНСэнЯр-п
    ZILL   1-02-00036-A        1      ЗИЛ ао
    ZVEZ   1-01-00169-D     1000   ЗВЕЗДА ао

    <class 'pandas.core.frame.DataFrame'>
    Index: 264 entries, ABRD to ZVEZ
    Data columns (total 3 columns):
    REGNUMBER    255 non-null object
    LOTSIZE      264 non-null int64
    SHORTNAME    264 non-null object
    dtypes: int64(1), object(2)
    memory usage: 8.2+ KB
