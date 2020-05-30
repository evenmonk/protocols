#!/usr/bin/env python3

import os
import re
import ssl
import base64
import socket
import shutil
import argparse

# список расширений файлов
EXTENSIONS = {'image': {'png': 'png', 'gif': 'gif', 'x-icon': 'ico', 'jpeg': ['jpeg', 'jpg'],
                        'svg+xml': 'svg', 'tiff': 'tiff', 'webp': 'webp', 'bmp': 'bmp'},
                'video': {'x-msvideo': 'avi', 'mpeg': ['mp3', 'mpeg'], 'ogg': 'ogv', 'webm': 'webm'},
                'application': {'zip': 'zip', 'xml': 'xml', 'octet-stream': 'bin', 'x-bzip': 'bz',
                                'msword': 'doc', 'epub+zip': 'epub', 'javascript': 'js', 'json': 'json',
                                'pdf': 'pdf', 'vnd.ms-powerpoint': 'ppt', 'x-rar-compressed': 'rar',
                                'x-sh': 'sh', 'x-tar': 'tar'},
                'audio': {'x-wav': 'wav', 'ogg': 'oga'},
                'text': {'css': 'css', 'csv': 'csv', 'html': 'html', 'plain': 'txt'}}

# класс, обрабатывающий ошибку протокола pop3
class POP3Exception(Exception):
    def __init__(self, message):
        # отсылает к ошибке в классе Exception
        super().__init__(message)


class MailStruct:
    def __init__(self, mail_from, mail_to, mail_subject,
                 mail_date, mail_size, original_headers):
        # от кого
        self.mail_from = mail_from
        # кому
        self.mail_to = mail_to
        # тема письма
        self.mail_subject = mail_subject
        # дата отправки
        self.mail_date = mail_date
        # размер письма
        self.mail_size = mail_size
        # заголовки
        self.original_headers = original_headers

    def __repr__(self):
        # Переопределяем представление объекта
        headers = ('From: {}\n'
                   'To: {}\n'
                   'Subject: {}\n'
                   'Date: {}\n'
                   'Mail Size: {} bytes\n').format(
            self.mail_from,
            self.mail_to,
            self.mail_subject,
            self.mail_date,
            self.mail_size)
        return headers

# вывести список команд
def print_help():
    print(
        """
        ---------------------------------------------------
        Список команд:
        EXIT - выйти из программы
        HELP - показать список команд
        LIST - получить список писем с основной информацией 
                (от кого, кому, когда пришло, тема письма)
        TOP [номер письма] [количество строк письма] 
            - показать указанное число строк письма.
        RECV [номер письма] - скачать указанное письмо
        RECV ALL - скачать все письма
        ---------------------------------------------------
        """
    )

# вывести список сообщений
def print_list(letters_info):
    for letter_number in range(len(letters_info)):
        print('\n', '\t\t\t Message № {}'.format(letter_number + 1))
        try:
            print(letters_info[letter_number], '\n')
        except UnicodeEncodeError:
            print('Wrong encoding')

# вывести несколько первых строк письма
def print_top(channel, letter_number, lines_count):
    if lines_count is None:
        # Если пользователь не указал количество строк, показываем все строки сообщения
        send(channel, 'TOP {}'.format(letter_number))
    else:
        send(channel, 'TOP {} {}'.format(letter_number, lines_count))
    # возвращаем полученное сообщение
    letter = '\n'.join(recv_multiline(channel))
    # определяем тело и заголовки сообщения
    headers, *body = letter.split('\n\n')
    # соединяем тело в одну строку
    body = '\n\n'.join(body)
    # регулярное выражение для имени файла
    file_name_regular = re.compile('filename="(.+?)"', flags=re.IGNORECASE)
    # регулярное выражение для кодировки
    encoding_regular = re.compile('Content-Transfer-Encoding: (.+)', flags=re.IGNORECASE)
    # регулярное выражение для base64
    base64_regular = re.compile(r'=\?(.*?)\?b', flags=re.IGNORECASE)
    # регулярное выражение для mime-типа
    content_type_regular = re.compile('Content-Type: (.+?)/(.+?)[;,\n]', flags=re.IGNORECASE)
    # регулярное выражение для разделителя
    boundary_regular = re.compile('boundary="(.*?)"')

    # поиск границы
    boundary = re.search(boundary_regular, headers)
    if not boundary:
        # если не нашли, создаем самостоятельно
        boundary = 'boundary'
    else:
        boundary = boundary.group(1)

    if 'Content-Type: multipart/mixed' in headers:
        body = body.split('--' + boundary + '\n')
        body[-1] = body[-1][:len(body[-1]) - len(boundary) - 4]
        if body[0] == '\n':
            body.pop(0)

        for attachment in body:
            attachment_data = attachment.split('\n\n')
            if len(attachment_data) < 2:
                continue
            
            # данные вложений
            attachment_data = attachment_data[1]
            # кодировка
            encoding = encoding_regular.search(attachment).group(1)
            # имя файла
            file_name = file_name_regular.search(attachment)

            if not file_name:
                content_info = content_type_regular.search(attachment)
                c_type = content_info.group(1)
                extension = EXTENSIONS[c_type][content_info.group(2)]
                file_name = "Letter {}.{}".format(letter_number, extension)
            else:
                continue

            if encoding == "base64":
                print(base64.b64decode(attachment_data))
            else:
                print(attachment_data)
    else:
        content_info = content_type_regular.search(headers)
        c_type = content_info.group(1)
        extension = EXTENSIONS[c_type][content_info.group(2)]
        encoding = encoding_regular.search(headers).group(1)

        if encoding == "base64":
            print(base64.b64decode(body))
        else:
            print(body)

# скачать письмо
def recv_letter(channel, letter_number, letter_info):
    # посылаем команду RETR с номером нужного письма
    send(channel, 'RETR {}'.format(letter_number))
    # полученное сообщение
    letter = '\n'.join(recv_multiline(channel))
    headers, *body = letter.split('\n\n')
    body = '\n\n'.join(body)

    

    file_name_regular = re.compile('filename="(.+?)"', flags=re.IGNORECASE)
    encoding_regular = re.compile('Content-Transfer-Encoding: (.+)', flags=re.IGNORECASE)
    base64_regular = re.compile(r'=\?(.*?)\?b', flags=re.IGNORECASE)
    content_type_regular = re.compile('Content-Type: (.+?)/(.+?)[;,\n]', flags=re.IGNORECASE)
    boundary_regular = re.compile('boundary="(.*?)"')

    boundary = re.search(boundary_regular, letter_info.original_headers)
    if not boundary:
        boundary = 'boundary'
    else:
        boundary = boundary.group(1)

    folder = 'Letter {}'.format(letter_number)
    try:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.mkdir(folder)
    except Exception as er:
        print(er)

    try:
        with open('{}/Letter {} info.{}.txt'.format(folder, letter_number, boundary), mode='w') as file:
            file.write(repr(letter_info))
    except Exception as er:
        print(er)

    if 'Content-Type: multipart/mixed' in letter_info.original_headers:

        body = body.split('--' + boundary + '\n')
        body[-1] = body[-1][:len(body[-1]) - len(boundary) - 4]
        if body[0] == '\n':
            body.pop(0)

        for attachment in body:
            attachment_data = attachment.split('\n\n')
            if len(attachment_data) < 2:
                continue

            attachment_data = attachment_data[1]

            encoding = encoding_regular.search(attachment).group(1)

            file_name = file_name_regular.search(attachment)

            if not file_name:
                content_info = content_type_regular.search(attachment)
                c_type = content_info.group(1)
                extension = EXTENSIONS[c_type][content_info.group(2)]
                file_name = "Letter {}.{}".format(letter_number, extension)

            else:
                file_name = file_name.group(1)

            if base64_regular.match(file_name):
                file_name = decode_inline_base64(file_name)

            with open('{}/{}'.format(folder, file_name), mode='wb') as file:
                if encoding == "base64":
                    file.write(base64.b64decode(attachment_data))
                else:
                    file.write(attachment_data.encode())
    else:
        content_info = content_type_regular.search(letter_info.original_headers)
        c_type = content_info.group(1)
        extension = EXTENSIONS[c_type][content_info.group(2)]
        file_name = "Letter {}.{}".format(letter_number, extension)
        encoding = encoding_regular.search(letter_info.original_headers).group(1)

        with open('{}/{}'.format(folder, file_name), mode='wb') as file:
            if encoding == "base64":
                file.write(base64.b64decode(body))
            else:
                file.write(body.encode())

# скачать все письма
def recv_all(channel, letters_info):
    for letter_number in range(1, len(letters_info) + 1):
        print(letter_number)
        recv_letter(channel, letter_number, letters_info[letter_number - 1])
    print('Successful')

# информация о письме
def get_info(channel):
    letters_struct = []
    # команда LIST для получения списка писем
    send(channel, 'LIST')
    for line in recv_multiline(channel):
        # из строки ответа забираем номер письма и его размер
        msg_id, msg_size = map(int, line.split())
        send(channel, 'TOP {} 0'.format(msg_id))
        headers = recv_multiline(channel)
        headers = '\n'.join(headers)
        important_headers = ['From', 'To', 'Subject', 'Date']
        important_headers_values = []
        # выборка нужных заголовков
        for header in important_headers:
            important_headers_values.append(
                find_header(header, headers) or 'unknown')
        important_headers_values = list(
            map(decode_inline_base64, important_headers_values))
        # определяем от кого, кому, тему сообщения и дату
        msg_from, msg_to, msg_subj, msg_date \
            = important_headers_values
        # добавляем эту информацию в струкруту письма
        letters_struct.append(MailStruct(
            msg_from, msg_to, msg_subj, msg_date, msg_size, headers))
    return letters_struct

# улучшение читаемости получаемых заголовков
def regexp_post_processing(s):
    flags = re.IGNORECASE | re.MULTILINE | re.DOTALL
    return re.sub(r'^\s*', '', s.strip(), flags=flags).replace('\n', '')

# получение нужных заголовков
def find_header(header, headers):
    flags = re.IGNORECASE | re.MULTILINE | re.DOTALL
    match = re.search(r'^{}:(.*?)(?:^\w|\Z|\n\n)'
                      .format(header), headers, flags)
    if match:
        return regexp_post_processing(match.group(1))


# декодирование base64
def decode_inline_base64(value):
    def replace(match):
        # первая группа - кодировка
        encoding = match.group(1).lower()
        # вторая группа - подстрока в base64
        b64raw = match.group(2)
        raw = base64.b64decode(b64raw.encode())
        try:
            # перевод из байт в строку
            return raw.decode(encoding)
        except Exception as ex:
            print(ex)
            return match.group(0)
    # ищем в строке закодированные в base64 подстроки,
    # применяем к ним функцию replace, которая формирует дешифрованную подстроку
    return re.sub(r'=\?(.*?)\?b\?(.*?)\?=', replace, value, flags=re.IGNORECASE)


# отправка команды
def send(channel, command):
    channel.write(command)
    channel.write('\n')
    # очищаем буфер
    channel.flush()

# получение однострочного ответа сервера
def recv_line(channel):
    response = channel.readline()[:-2]
    if response.startswith('-ERR'):
        raise POP3Exception(response)

# получение много 
def recv_multiline(channel):
    recv_line(channel)
    lines = []
    while True:
        # читаем линию без знака переноса строки
        line = channel.readline()[:-2]
        # если достигли конца письма, то выходим
        if line == '.':
            break
        lines.append(line)
    return lines

# аутентификация пользователя
def authentication(channel, username, password):
    send(channel, 'USER {}'.format(username))  # отправляем имя пользователя
    recv_line(channel)  # получаем ответ сервера
    channel.write('PASS {}\n'.format(password))  # отправляем пароль
    channel.flush()  # очищаем буфер файл-подобного объекта сокета
    recv_line(channel)  # получаем ответ сервера


def main(host='pop3.yandex.ru'):
    # получаем ip pop3-сервера
    addr = socket.gethostbyname(host)
    # создаем udp-сокет
    sock = socket.socket()
    # устанавливаем таймаут
    sock.settimeout(10)
    # оборачиваем в ssl
    sock = ssl.wrap_socket(sock)
    port = 995
    sock.connect((addr, port))
    # превращаем сокет в файл-подобный объект
    channel = sock.makefile('rw', newline='\r\n', encoding='utf-8')
    # получаем от сервера ответ
    recv_line(channel)
    username = input('Enter username: ')
    password = input('Enter password: ')
    authentication(channel, username, password)
    letters_info = get_info(channel)
    print_help()
    top_req_exp = re.compile('TOP (\d+) (\d+)')
    top_req_exp_cut = re.compile('TOP (\d+)')
    recv_req_exp = re.compile('RECV (\d+)')
    while True:
        command = input().upper()
        if command == 'EXIT':
            # заканчиваем работу программы
            print('Bye!')
            exit()
        elif command == 'HELP':
            # выводим список команд
            print_help()
        elif command == 'LIST':
            # выводим список сообщений
            print_list(letters_info)
        elif top_req_exp.match(command):
            info = top_req_exp.match(command)
            print_top(channel, info.group(1), info.group(2))
        elif top_req_exp_cut.match(command):
            info = top_req_exp_cut.match(command)
            print_top(channel, info.group(1), None)
        elif recv_req_exp.match(command):
            info = recv_req_exp.match(command)
            recv_letter(channel, int(info.group(1)), letters_info[int(info.group(1)) - 1])
        elif command == 'RECV ALL':
            # скачиваем все сообщения
            recv_all(channel, letters_info)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('host', help='Pop3 server address')
    args = argparser.parse_args()
    try:
        main(args.host)
    except KeyboardInterrupt:
        print('[-] Interrupted')
    except Exception as err:
        print('Error:', err)