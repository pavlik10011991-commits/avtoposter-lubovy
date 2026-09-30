#!/usr/bin/env python3
"""Находит бизнес-подключение бота (Telegram Business → Чат-боты) и сохраняет его id в секрет TG_BUSINESS_CONN."""
import json, os, subprocess, sys
import requests

base = f"https://api.telegram.org/bot{os.environ['TG_BOT_TOKEN']}"
import time
conns, offset, deadline = [], None, time.time() + 900
while time.time() < deadline and not conns:
    params = {"allowed_updates": json.dumps(["business_connection"]), "timeout": 25}
    if offset: params["offset"] = offset
    r = requests.get(f"{base}/getUpdates", params=params, timeout=40).json()
    if not r.get("ok"):
        print("Ошибка Telegram:", r.get("description")); sys.exit(1)
    for u in r["result"]:
        offset = u["update_id"] + 1
        if "business_connection" in u: conns.append(u["business_connection"])
    print("жду подключение… получено обновлений:", len(r["result"]))
if not conns:
    print("Подключений не найдено. В Телеграме: Настройки → Telegram для бизнеса → Чат-боты → добавьте бота "
          "и разрешите «Управление историями». Затем запустите снова (в течение суток).")
    sys.exit(1)
c = conns[-1]
rights = c.get("rights") or {}
print(f"Подключение от {c['user'].get('first_name')} (@{c['user'].get('username')}), активно: {c.get('is_enabled')}, "
      f"истории: {rights.get('can_manage_stories')}")
if not c.get("is_enabled") or not rights.get("can_manage_stories"):
    print("Нужно включить право «Управление историями» для бота в Telegram для бизнеса."); sys.exit(1)
subprocess.run(["gh", "secret", "set", "TG_BUSINESS_CONN", "--repo", os.environ["GITHUB_REPOSITORY"]], input=c["id"], text=True, check=True)
print("✔ Секрет TG_BUSINESS_CONN сохранён. Сторис в личный Телеграм будут публиковаться автоматически.")
