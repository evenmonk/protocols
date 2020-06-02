#!/usr/bin/env python3

import sys
import json
import requests
import argparse


def get_inf(name, token):
    inf = None
    args = {
        'user_id': name,
        'access_token': token,
        'fields': 'city, bdate, counters',
        'v': '5.76'
    }
    try:
        info = requests.get("https://api.vk.com/method/users.get", args)
    except requests.exceptions.SSLError as e:
        print("Something wrong with SSL. Try again later")
        sys.exit(1)
    except requests.ConnectionError as e:
        print("Something wrong with connection. Try again later")
        sys.exit(1)
    return info.json()


def get_token_from_file():
    with open("token.txt", "r", encoding="utf-8") as file:
        return file.read()

def handle_responce(self):
    result = "Информация о пользователе: \n"
    result += "----------------------------------- \n"
    result += "ID пользователя: " + str(self["response"][0]["id"]) + "\n"
    result += "Имя: " + str(self["response"][0]["first_name"]) + "\n"
    result += "Фамилия: " + str(self["response"][0]["last_name"]) + "\n"
    result += "Дата рождения: " + self["response"][0]["bdate"] + "\n"
    result += "Город: " + self["response"][0]["city"]["title"] + "\n"
    result += "Количество видео: " + str(self["response"][0]["counters"]["videos"]) + "\n"
    result += "Количество аудио: " + str(self["response"][0]["counters"]["audios"]) + "\n"
    result += "Количество подарков: " + str(self["response"][0]["counters"]["gifts"]) + "\n"
    result += "Количество подписок: " + str(self["response"][0]["counters"]["subscriptions"]) + "\n"
    result += "Количество альбомов: " + str(self["response"][0]["counters"]["albums"]) + "\n"
    result += "Количество фотографий: " + str(self["response"][0]["counters"]["photos"]) + "\n"
    result += "Количество подписчиков: " + str(self["response"][0]["counters"]["followers"]) + "\n"
    result += "Количество друзей: " + str(requests.get("https://api.vk.com/method/friends.get", {
        'user_id': args.id,
        'access_token': token,
        'v': '5.76'
         }).json()["response"]["count"]) + "\n"
    result += "----------------------------------- \n"
    return result

if __name__ == '__main__':
    parcer = argparse.ArgumentParser()
    parcer.add_argument("id", help = "ID пользователя")
    args = parcer.parse_args()
    if args.id:
        token = get_token_from_file()
        response = get_inf(args.id, token)
        result = handle_responce(response)
        print("\n" + result)
        