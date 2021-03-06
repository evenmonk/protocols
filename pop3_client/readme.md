# POP3  Client
POP3 Клиент для получения информации о письмах с почтового сервера. 
Использует 995 ssl порт pop3.
* Может показать заголовки: тему, дату, отправителя и т. п. 
* Может показать TOP (несколько строк) сообщения. 
* Может скачать письмо с вложением.

> Необходим интерпретатор Python версии не ниже, чем 3.6

## Запуск клиента
```
$ python client.py host
```

Позиционные аргументы:

Argument | Description
-------- | ----------
host | pop3 адрес сервера

Опциональные аргументы:

Argument | Description
-------- | ----------
-h, --help | Показать справочное сообщение

Использование:

Argument | Description
-------- | ----------
EXIT | выйти из программы
HELP | показать список команд
LIST | получить список писем с основной информацией
TOP [номер письма] [количество строк письма] | показать указанное число строк письма.
RECV [номер письма] | скачать указанное письмо
RECV ALL | скачать все письма


## Пример запуска
![https://imgur.com/a/zBZIC6E](https://github.com/evenmonk/protocols/blob/master/pop3_client/example.png)

Выполнил студент группы МО-202 МЕН-282203 Эрделевский Евгений