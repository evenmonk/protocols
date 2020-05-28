#!/usr/bin/env python3

import sys
import socket
import threading
import argparse
import struct
import queue
import time

# Колиество секунд с 01.01.1900 (начало отсчета в NTP) по 01.01.1970 (начало UNIX-времени)
SNTP_DELTA = 2208988800
                                                                 
OFFSET = 0

class SNTPPacket:
    PACKET_FORMAT = ">3B b 5I 3Q"

    def __init__(self, transmit_timestamp, originate_timestamp):
        # кодовое предупреждение о надвигающейся високосной секунде, 
        self.leap = 0
        # номер версии NTP
        self.version = 4
        # мод (3 - клиент, 4 - сервер)
        self.mode = 4
        # Слой (уровень) нашего сервера (1 - первичный сервер, 2 - вторичный)
        self.stratum = 2
        # Интервал между сообщениями от сервера копируется из запроса клиента
        self.poll = 0
        # Точность устанавливается как -ln от значащих бит сервера справа от запятой
        self.precision = 0
        # Время приема-передачи (RTT)
        self.root_delay = 0
        # Номинальная ошибка
        self.root_dispersion = 0
        # Идентификатор эталона
        self.reference_id = 0
        # Время, когда наше время было установлено или поправлено
        self.reference_timestamp = 0
        if not originate_timestamp:
            self.originate_timestamp = time.time()
        else:
            self.originate_timestamp = 0
        # Время прихода запроса на сервер
        self.receive_timestamp = 0
        # Время отправки ответа
        self.transmit_timestamp = 0

    def __bytes__(self):
        return struct.pack(SNTPPacket.PACKET_FORMAT,
                           (self.leap << 6 | self.version << 3 | self.mode),
                           self.stratum,
                           self.poll,
                           self.precision,
                           self.root_delay,
                           self.root_dispersion,
                           self.reference_id,
                           self.reference_timestamp,
                           self.reference_timestamp,
                           self.originate_timestamp,
                           SNTPPacket.to_fractional(
                               self.receive_timestamp + OFFSET),
                           SNTPPacket.to_fractional(
                               time.time() + SNTP_DELTA + OFFSET)
                           )

    @classmethod
    def parse_packet(cls, packet):
        if len(packet) < 48:
            return None
        version = (packet[0] & 56) >> 3
        mode = packet[0] & 7
        if mode != 3:
            return None
        transmit_timestamp = int.from_bytes(packet[40:48], 'big')
        return SNTPPacket(transmit_timestamp,
                        int(time.time() + SNTP_DELTA))

    @classmethod
    def to_fractional(cls, timestamp):
        return int(timestamp * (2 ** 32))


class SNTPServer:
    def __init__(self, port, workers=10):
        self.is_working = True
        self.server_port = port

        self.to_send = queue.Queue()
        self.received = queue.Queue()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', self.server_port))

        self.receiver = threading.Thread(target=self.receive_request)
        self.workers = [threading.Thread(target=self.handle_request) for _ in
                        range(workers)]

    def start(self):
        for worker in self.workers:
            worker.setDaemon(True)
            worker.start()
        self.receiver.setDaemon(True)
        self.receiver.start()
        print(f"listening to {self.server_port} port")
        while self.is_working:
            pass

    def handle_request(self):
        while self.is_working:
            try:
                packet, address = self.received.get(block=False)
            except queue.Empty:
                pass
            else:
                if packet:
                    self.sock.sendto(bytes(packet), address)

    def receive_request(self):
        while self.is_working:
            try:
                data, addr = self.sock.recvfrom(1024)
                self.received.put((SNTPPacket.parse_packet(data), addr))
                print(f'Request:\nIP: {addr[0]}\nPort: {addr[1]}\n')
            except socket.error:
                return

    def stop(self):
        self.is_working = False
        self.receiver.join()
        for w in self.workers:
            w.join()
        self.server.close()

    def main(self):
        server = SNTPServer(self)
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()

if __name__ == "__main__":
    try:
        with open('conf.txt') as f:
            OFFSET = int(f.readline())
    except Exception as e:
        print('ERROR: {}'.format(e))
    finally:
        # устанавливаем время сдвига
        print('offset: {} sec.'.format(OFFSET))
    SNTPServer.main(123)