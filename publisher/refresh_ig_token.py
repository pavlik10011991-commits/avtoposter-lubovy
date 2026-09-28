#!/usr/bin/env python3
"""Продлевает токен Инстаграма (живёт 60 дней) и печатает новый в файл для шага `gh secret set`."""
import os
import sys

import requests

tok = os.getenv("IG_ACCESS_TOKEN", "").strip()
if not tok:
    sys.exit("нет IG_ACCESS_TOKEN")
j = requests.get("https://graph.instagram.com/refresh_access_token",
                 params={"grant_type": "ig_refresh_token", "access_token": tok}, timeout=30).json()
if "access_token" not in j:
    sys.exit(f"Не удалось продлить токен: {j.get('error', j)}")
days = int(j.get("expires_in", 0)) // 86400
with open(os.getenv("OUT", "new_token.txt"), "w") as f:
    f.write(j["access_token"])
print(f"Токен продлён, действует ещё {days} дн.")
