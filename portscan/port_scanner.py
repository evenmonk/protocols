#!/usr/bin/env python3

import socket
from re import match
from struct import unpack, pack
from multiprocessing import Pool
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description='Сканер TCP и UDP портов')
    parser.add_argument('host', type=str, help='Целевой хост для сканирования')
    parser.add_argument('-l', '--start_port', default=1, type=int, help='Нижняя граница сканируемых портов')
    parser.add_argument('-r', '--end_port', default=150, type=int, help='Верхняя граница сканируемых портов')
    parser.add_argument('-t', '--timeout', default=100, type=int, help='Timeout of response in milliseconds')
    parser.add_argument('-tcp', action='store_true', help='Сканировать открытые TCP порты')
    parser.add_argument('-udp', action='store_true', help='Сканировать открытые UDP порты')
    parser.add_argument('-p', '--processes', default=5, type=int, help='Количество потоков')
    
    args = parser.parse_args()
    if not args.tcp and not args.udp:
        args.tcp = args.udp = True
    scanner = PortScanner(args.host, args.timeout)
    pool = Pool(args.processes)
    if args.tcp:
        scan = pool.imap(scanner.tcp_request, range(args.start_port, args.end_port + 1))
        for port, protocol in scan:
            if protocol:
                print(f'TCP port {port} is open. Protocol: {protocol}')
    if args.udp:
        scan = pool.imap(scanner.udp_request, range(args.start_port, args.end_port + 1))
        for port, protocol in scan:
            if protocol:
                print(f'UDP port {port} is open. Protocol: {protocol}')

class PortScanner:

    DNS_TRANSACTION_ID = b'\x13\x37'

    DNS_PACKET = DNS_TRANSACTION_ID + \
                b'\x01\x00\x00\x01' + \
                b'\x00\x00\x00\x00\x00\x00' + \
                b'\x02\x65\x31\x02\x72\x75' + \
                b'\x00\x00\x01\x00\x01'

    TCP_PACKETS = {
        'HTTP': b'\0',
        'SMTP': b'EHLO',
        'DNS': DNS_PACKET,
        'POP3': b'AUTH'
    }

    UDP_PACKETS = {
        'SNTP': b'\x1b' + 47 * b'\0',
        'DNS': DNS_PACKET
    }

    PROTOCOL_CHECKER = {
        'HTTP': lambda packet: b'HTTP' in packet,
        'POP3': lambda packet: packet.startswith(b'+'),
        'DNS' : lambda packet: packet.startswith(PortScanner.DNS_TRANSACTION_ID),
        'SMTP': lambda packet: match(b'[0-9]{3}', packet[:3]),
        'SNTP': lambda packet: PortScanner.__sntp_check(packet),
    }

    def __init__(self, dest, timeout):
        self.dest = dest
        self.timeout = timeout / 1000

    def tcp_request(self, port):
        socket.setdefaulttimeout(self.timeout)
        for prot, packet in PortScanner.TCP_PACKETS.items():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((self.dest, port))
                except socket.timeout:
                    return (port, None)
                try:
                    if prot == 'DNS':
                        packet = pack('!H', len(packet)) + packet
                    s.send(packet)
                    packet = s.recv(128)
                    if prot == 'DNS':
                        packet = packet[2:]
                    if PortScanner.PROTOCOL_CHECKER[prot](packet):
                        return (port, prot)
                except socket.error:
                    continue
        return (port, 'Unknown protocol')

    def udp_request(self, port):
        socket.setdefaulttimeout(self.timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            for prot, packet in PortScanner.UDP_PACKETS.items():
                s.sendto(packet, (self.dest, port))
                try:
                    if PortScanner.PROTOCOL_CHECKER[prot](s.recv(128)):
                        return (port, prot)
                except socket.error:
                    continue
        return (port, None)

    @staticmethod
    def __sntp_check(packet):
        try:
            unpack('!BBBb11I', packet)
            return True
        except Exception as e:
            return False


if __name__ == "__main__":
    try:
        main()
    except PermissionError:
        print('Необходимы права администратора')
    except KeyboardInterrupt:
        print('[-] Interrupted')