#!/usr/bin/env python3
"""
Один раз: вход в Телеграм аккаунтом администратора канала, чтобы публиковать сторис.
Запускать в обычном Терминале на компьютере (где открывается Телеграм):

    pip3 install telethon
    python3 login_telegram.py

Скрипт спросит api_id, api_hash (с my.telegram.org), номер телефона и код из Телеграма,
и выдаст длинную строку — её нужно вставить в GitHub → Settings → Secrets → TG_SESSION.
Строка = доступ к аккаунту. Никому её не пересылайте и не храните в файлах.
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("api_id: ").strip())
api_hash = input("api_hash: ").strip()
with TelegramClient(StringSession(), api_id, api_hash) as client:
    me = client.get_me()
    print(f"\nВход выполнен: {me.first_name} (@{me.username})")
    print("\nСкопируйте строку ниже целиком в секрет TG_SESSION:\n")
    print(client.session.save())
