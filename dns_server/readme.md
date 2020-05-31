# DNS Server
Кэширующий DNS Server
Сервер прослушивает 53 UDP порт. 
При первом запуске кэш пустой. 

> Необходим интерпретатор Python версии не ниже, чем 3.6 и библиотека IPy

## Запуск сервера
```sh
$ python dns.py [-h] [-p P] [-f F]
```

Список аргументов:

Argument | Description
-------- | ----------
-h, --help | Показать справочное сообщение
-p PORT  |  Порт для прослушивания подключений
-f FORWARDER | IP:Port форвардера. Например, 8.8.8.8:53

## Пример запуска
Например, был запущен сервер на 2222 порту. Затем вы можете сделать запросы к нему, набрав следующую команду (получить А записи от google.com):
```
dig +notcp @127.0.0.1 -p 2222 google.com A
```
Список остальных типов записей указан в файле resolver.py
![https://imgur.com/a/uJUTWsS](https://github.com/evenmonk/protocols/blob/master/dns_server/example.png)
![https://imgur.com/a/CPpKlyz](https://github.com/evenmonk/protocols/blob/master/dns_server/example2.jpg)

Выполнил студент группы МО-202 МЕН-282203 Эрделевский Евгений
