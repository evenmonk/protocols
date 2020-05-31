#!/usr/bin/env python3

import json
import socket
import requests
from struct import unpack
from urllib.request import urlopen
from argparse import ArgumentParser

ICMP_ECHO_REQUEST = b'\x08\x00\x0b\x27\xeb\xd8\x01\x00'

# серые адреса
PRIVATE_NETWORKS = {
    ('10.0.0.0', '10.255.255.255'),
    ('172.16.0.0', '172.31.255.255'),
    ('192.168.0.0', '192.168.255.255'),
    ('127.0.0.0', '127.255.255.255')
}

# парсинг аргументов
def get_parcer():
    argparser = ArgumentParser(description="Trace Autonomous Systems")
    argparser.add_argument("target", type=str, help="Целевой хост")
    argparser.add_argument("-hops", default=52, type=int, help="Максимальное значение прыжков (TTL)")
    argparser.add_argument("-timeout", default=5, type=int, help="Таймаут ответа в секундах")
    return argparser

# проверка на белый ip
def is_white_ip(ip):
    for network in PRIVATE_NETWORKS:
        if network[0] <= ip <= network[1]:
            return False
    return True

# информация об ip
def get_ip_info(ip):
    info = json.loads(requests.get("http://ipinfo.io/{0}/json".format(ip)).content)
    msg = "\t {0} {1} {2}".format(info['country'], info['region'], info['city'])
    if "org" in info:
        if info["org"] != "":
            msg += " Organisation: {}".format(info["org"])
    if "loc" in info:
        if info["loc"] != "":
            msg += " Location: {}".format(info["loc"])
    return msg

# построение маршрута
def traceroute(target, hops, timeout):
    target = socket.gethostbyname(target)
    current_address = None
    ttl = 1
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
        # по умолчанию таймаут = 5
        sock.settimeout(timeout)
        # пока не достигли целевого хоста 
        while ttl != hops and current_address != target:
            # отправляем запросы
            sock.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
            sock.sendto(ICMP_ECHO_REQUEST, (target, 1))
            try:
                packet, adr = sock.recvfrom(1024)
                current_address = adr[0]
                message = "{0} {1}".format(ttl, current_address)
                if is_white_ip(current_address):
                    message += get_ip_info(current_address)
                yield message
            except socket.timeout:
                yield '*****'
                exit(2)
            ttl += 1

def main():
    argparser = get_parcer()
    args = argparser.parse_args()
    for message in traceroute(args.target, args.hops, args.timeout):
        print(message)

if __name__ == '__main__':
    main()