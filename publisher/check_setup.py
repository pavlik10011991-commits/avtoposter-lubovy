#!/usr/bin/env python3
"""Проверка подключения: бот, канал, сессия для сторис, Инстаграм. Ничего не публикует."""
import asyncio
import os
import sys

import requests

IG_API = os.getenv("IG_API_VERSION", "v23.0")
ok = True


def line(good, text):
    global ok
    ok &= bool(good) or good is None
    print(("✔ " if good else ("• " if good is None else "✖ ")) + text)


def has(*names):
    return all(os.getenv(n, "").strip() for n in names)


# ── бот и канал
if has("TG_BOT_TOKEN", "TG_CHANNEL"):
    base = f"https://api.telegram.org/bot{os.environ['TG_BOT_TOKEN']}"
    me = requests.get(f"{base}/getMe", timeout=30).json()
    line(me.get("ok"), f"бот: @{me.get('result', {}).get('username', '?')}" if me.get("ok")
         else f"бот: токен не подходит ({me.get('description')})")
    if me.get("ok"):
        ch = os.environ["TG_CHANNEL"]
        chat = requests.get(f"{base}/getChat", params={"chat_id": ch}, timeout=30).json()
        line(chat.get("ok"), f"канал: {chat['result'].get('title')}" if chat.get("ok")
             else f"канал {ch}: не найден ({chat.get('description')})")
        mem = requests.get(f"{base}/getChatMember", params={"chat_id": ch, "user_id": me["result"]["id"]},
                           timeout=30).json()
        r = mem.get("result", {})
        line(r.get("status") == "administrator" and r.get("can_post_messages", True),
             "бот — администратор с правом публикации" if r.get("status") == "administrator"
             else "бот не администратор канала — добавьте его в админы")
else:
    line(False, "нет секретов TG_BOT_TOKEN / TG_CHANNEL")

# ── сторис канала
if has("TG_SESSION", "TG_API_ID", "TG_API_HASH", "TG_CHANNEL"):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.tl import functions

    async def stories():
        c = TelegramClient(StringSession(os.environ["TG_SESSION"]), int(os.environ["TG_API_ID"]),
                           os.environ["TG_API_HASH"])
        await c.connect()
        try:
            if not await c.is_user_authorized():
                line(False, "сессия для сторис недействительна — заново запустите login_telegram.py")
                return
            me = await c.get_me()
            line(True, f"аккаунт для сторис: {me.first_name} (@{me.username})")
            peer = await c.get_input_entity(os.environ["TG_CHANNEL"])
            try:
                res = await c(functions.stories.CanSendStoryRequest(peer=peer))
                left = getattr(res, "count_remains", None)
                line(True, "канал может публиковать сторис" + (f", осталось на сегодня: {left}" if left is not None else ""))
            except Exception as e:
                line(False, f"канал пока не может публиковать сторис: {e} — нужны бусты (уровень ≥ 1)")
        finally:
            await c.disconnect()

    asyncio.run(stories())
else:
    line(None, "сторис в ТГ не настроены (TG_SESSION / TG_API_ID / TG_API_HASH) — посты работают и без них")

# ── Инстаграм
if has("IG_ACCESS_TOKEN"):
    j = requests.get(f"https://graph.instagram.com/{IG_API}/me",
                     params={"fields": "user_id,username,account_type", "access_token": os.environ["IG_ACCESS_TOKEN"]},
                     timeout=30).json()
    if "error" in j:
        line(False, f"Инстаграм: токен не подходит ({j['error'].get('message')})")
    else:
        line(True, f"Инстаграм: @{j.get('username')} ({j.get('account_type')}), user_id = {j.get('user_id')}")
        if os.getenv("IG_USER_ID") and os.environ["IG_USER_ID"] != str(j.get("user_id")):
            line(False, f"IG_USER_ID в секретах не совпадает — поставьте {j.get('user_id')}")
        elif not os.getenv("IG_USER_ID"):
            line(False, f"добавьте секрет IG_USER_ID = {j.get('user_id')}")
else:
    line(None, "Инстаграм не настроен (IG_ACCESS_TOKEN)")

print("\nВсё готово к публикации" if ok else "\nЕсть что поправить — см. строки с ✖")
sys.exit(0 if ok else 1)
