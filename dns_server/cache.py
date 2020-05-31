#!/usr/bin/env python3

import os
import time
import copy
import string
import struct
import codecs
import calendar


NAME_OFFSET = b'\xc0\x0c'
PADDING = '11'

# время
def get_cur_time():
    return int(time.time())

# отступ
def set_padding(n):
    return (8 - len(n)) * '0' + n

# имя вопроса
def get_qname(record, packet=None):
    index, qname = 0, ''
    qname = ''
    try:
        while True:
            if record[index] == 0:
                break
            size = record[index]
            if set_padding(bin(size)[2:])[:2] == PADDING:
                offset = codecs.encode(record[index:index+2], 'hex').decode()
                offset = int(bin(int(offset, 16))[4:], 2)
                index, record = offset, packet
                continue
            index += 1
            for i in range(index, index+size):
                qname += chr(record[i])
            qname += '.'
            index += size
    except Exception:
        return ''
    return qname


class Cache:
    # изначально пустой
    def __init__(self):
        self._cache = {}
        self.outdate_time = 10
        self.used_qtypes = set()

    # добавить данные
    def push(self, qname, qtype, question, value):
        if qname not in self._cache:
            self._cache[qname] = {}
        self.used_qtypes.add(qtype)
        entity = CachedEntity(value, qtype, question)
        self._cache[qname][qtype] = entity
        return entity.get_inner_qnames()

    # проверка на то, содержатся ли уже данные в кэше
    def contains(self, qname, qtype):
        return qname in self._cache and qtype in self._cache[qname]

    # получить данные из кэша
    def get(self, qname, qtype, id):
        answer = b''
        is_outdated = False
        value = self._cache[qname][qtype]

        for field in value.sections:
            cur_time = get_cur_time()
            new_ttl = field.start_time + field.ttl - cur_time
            if new_ttl < self.outdate_time:
                is_outdated = True
                break
            field.set_ttl(new_ttl)
            field.start_time = cur_time
            
            answer += field.section
        if is_outdated:
            del value
            return None
        return self._process_head(value.head, id) + value.question + answer + value._additional

    def _process_head(self, head, id):
        return id + head[2:]

# определяет ttl, начальное время и секцию
class InnerEntity:
    def __init__(self, ttl, start_time, section):
        self.ttl        = ttl
        self.start_time = start_time
        self.section    = section

    def set_ttl(self, new_ttl):
        self.ttl = new_ttl
        self.section = self.section[:6] + struct.pack('>I', new_ttl) + self.section[10:]

# определяет поля вопрос, секция, их типы
class CachedEntity:
    def __init__(self, packet, qtype, question):
        self.question = question
        self.qtype = qtype
        self._raw_packet = packet
        self.sections = []
        self._additional = b''
        self.head = b''
        self._inner_qnames = []
        self._process_packet(packet)

    # обработать полученный пакет
    def _process_packet(self, packet):
        self.head = packet[:12]
        spacket = packet[12:]
        sections = self._parse_sections(self.head, spacket)

        for section in sections:
            self.sections.append(InnerEntity(self.get_raw_ttl(section), get_cur_time(), section))

    # разделение на секции
    def _parse_sections(self, head, packet):
        top_packet = head + packet
        question, packet = self._split_packet(packet, packet.find(b'\x00')+5)
        sections = []

        while len(packet) > 1:
            name, packet = self._split_packet(packet, packet.find(b'\x00'))
            info, packet = self._split_packet(packet, 8)
            rlength, packet = self._split_packet(packet, 2)
            rdata, packet = self._split_packet(packet, struct.unpack('>H', rlength)[0])

            self._process_rdata(info, rdata, top_packet)

            section = name + info + rlength + rdata
            sections.append(section)
        if sections[-1].startswith(b'\x00\x00'):
            sections = sections[:-1]
        return sections

    # обработка сырых данных
    def _process_rdata(self, info, rdata, packet):
        if self.qtype not in [15, 2]:
            return
        # отступ
        offset = codecs.encode(rdata[-2:], 'hex').decode()
        if offset != '':
            qname = self.__get_qname(rdata, packet)
            self._inner_qnames.append(qname)

    # внутренние поля
    def get_inner_qnames(self):
        return self._inner_qnames

    # получить имя вопроса
    def __get_qname(self, rdata, packet):
        ndata = rdata[2:] if self.qtype != 2 else rdata
        return get_qname(ndata, packet)

    # разделение пакета
    def _split_packet(self, packet, index):
        data = packet[:index]
        return data, packet[index:]

    # разделение секции
    def _split_section(self, section):
        rlength = struct.unpack('>H', section[10:12])[0]
        return section[:12+rlength], section[12+rlength:]

    # получение ttl
    def get_raw_ttl(self, section):
        ttl = section[6:10]
        return struct.unpack('>I', ttl)[0]