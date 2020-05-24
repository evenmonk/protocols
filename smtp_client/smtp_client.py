#!/usr/bin/env python3

import configparser
import socket
from ssl import wrap_socket
from base64 import b64encode

reader = configparser.ConfigParser(allow_no_value = True)
# считываем данные из конфига
with open('./conf/config.cfg', 'r', encoding='utf-8') as f:
    reader.read_file(f)

msg = reader['MESSAGE']
acc = reader['ACCOUNT']
login = acc['Login']
passw = acc['Password'].encode()
receivers = ','.join(reader['RECEIVERS'])
subject = msg['Subject']

# считываем текст из файла
with open(msg['Text'], 'r', encoding='cp1251') as f:
    text = f.read()

# обрабатываем точки в посылаемом тексте
if text[0] == '.':
	text = '.' + text
text = text.replace("\n.", "\n..")

# последовательность символов, разделяющих части сообщения
boundary = msg['Boundary']

# считываем прикрепленные картинки, документы и т.д.
attachments = ''
for attachment in msg['Attachments'].split('\n')[1:]:
    attachment = attachment.split(',')
    filename = attachment[0].strip()
    # тип многоцелевого расшерения интернет-почты
    mime_type = attachment[1].strip()
    with open(filename, 'rb') as f:
        filename = filename.replace("./conf/", "")
        file = b64encode(f.read())
        attachments += (f'Content-Disposition: attachment; filename="{filename}"\n'
        'Content-Transfer-Encoding: base64\n'
        f'Content-Type: {mime_type}; name="{filename}"\n\n'
        ) + file.decode() + f'\n--{boundary}'

# если не каждый символ из темы сообщения итерируемый, 
# то кодируем и декоридуем тему сообщения 
if not all(ord(i) < 128 for i in subject):
    subject = f'=?utf-8?B?{b64encode(subject.encode()).decode()}?='

# формируем итоговое сообщение, считав ранее необходимую информацию
# из config.cfg и text.txt
message = (
    f"From: {login}\n"
    f"To: {receivers}\n"
    f"Subject: {subject}\n"
    "MIME-Version: 1.0\n"
    f'Content-Type: multipart/mixed; boundary="{boundary}"\n\n'
    f"--{boundary}\n"
    "Content-Type: text/plain; charset=utf-8\n"
    "Content-Transfer-Encoding: 8bit\n\n"
    f"{text}\n"
    f"--{boundary}\n"
    f"{attachments}--\n."
)

# функция отправки команды сокету и принятия ответа от него
def request(sock, cmd, buffer_size=1024):
    sock.send(cmd + b'\n')
    return sock.recv(buffer_size).decode()

if __name__ == "__main__": 
    login = login.encode()
    # устанавливаем соединение по указанному адресу и порту
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock = wrap_socket(sock)
        server = reader['SERVER']
        sock.settimeout(float(server['Timeout']))
        sock.connect((server['Address'], int(server['Port'])))
        # посылаем приветственное сообщение 
        print(request(sock, b'EHLO test'))
        # логинимся
        print(request(sock, b'AUTH LOGIN'))
        print(request(sock, b64encode(login)))
        print(request(sock, b64encode(passw)))
        # указываем от кого посылается сообщение
        print(request(sock, b'MAIL FROM: ' + login))
        # указываем получателей
        for recipient in reader['RECEIVERS']:
            print(request(sock, b'RCPT TO: ' + recipient.encode()))
        # посылаем самое сообщение
        print(request(sock, b'DATA'))
        print(request(sock, message.encode()))
        print('Message sent')
