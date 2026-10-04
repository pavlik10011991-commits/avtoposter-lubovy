#!/usr/bin/env python3
"""Ждёт, пока Люба напишет боту (/start), и сохраняет её chat_id в секрет TG_ADMIN_CHAT_ID.
Туда бот присылает ошибки и сторис для ручной публикации, если Telegram Premium не активен."""
import json, os, subprocess, sys, time
import requests

base = f"https://api.telegram.org/bot{os.environ['TG_BOT_TOKEN']}"
me = requests.get(f"{base}/getMe", timeout=30).json()["result"]
print(f"Бот: @{me['username']}. Жду сообщение от @{os.environ.get('WANT_USER', 'lubovypr')}…", flush=True)
want = os.environ.get("WANT_USER", "lubovypr").lower()
offset, deadline, chat = None, time.time() + 3 * 3600, None
while time.time() < deadline and not chat:
    params = {"allowed_updates": json.dumps(["message"]), "timeout": 50}
    if offset: params["offset"] = offset
    r = requests.get(f"{base}/getUpdates", params=params, timeout=70).json()
    for u in r.get("result", []):
        offset = u["update_id"] + 1
        m = u.get("message") or {}
        if m.get("chat", {}).get("type") == "private" and (m.get("from", {}).get("username") or "").lower() == want:
            chat = m["chat"]["id"]
if not chat:
    print("Сообщение не пришло. Откройте бота в Телеграме, нажмите «Старт» и запустите снова."); sys.exit(1)
subprocess.run(["gh", "secret", "set", "TG_ADMIN_CHAT_ID", "--repo", os.environ["GITHUB_REPOSITORY"]], input=str(chat), text=True, check=True)
requests.post(f"{base}/sendMessage", data={"chat_id": chat, "text": "✅ Готово! Сюда буду присылать сторис для личного Телеграма, если не получится выложить автоматически, и сообщения об ошибках автопостера."}, timeout=30)
print("✔ TG_ADMIN_CHAT_ID сохранён")
