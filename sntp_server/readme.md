# Simple Network Time Protocol
Простой SNTP сервер, который врёт на N секуд указанных в файле conf.txt. 

>Необходим интерпретатор Python версии не ниже, чем 3.6

# Запуск сервера
> python server.py

Для проверки работоспособности сервера используется команда
> w32tm /stripchart /computer:127.0.0.1 /dataonly /samples:5

# Алгоритм
  - Получаем пакет от ОС
  - Изменяем 40-47 байты, содержащие информацию о времени на N секунд
  - Пробрасываем пакет клиенту

# Пример запуска
![https://imgur.com/a/DrkL3vI](https://github.com/evenmonk/protocols/blob/master/sntp_server/example.png)

Выполнил студент группы МО-202 МЕН-282203 Эрделевский Евгений
