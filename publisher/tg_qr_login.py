#!/usr/bin/env python3
"""
Вход в Телеграм аккаунтом админа канала по QR-коду (запускается в GitHub Actions: «Вход в Телеграм»).
QR появляется в логе → Телеграм на телефоне: Настройки → Устройства → Подключить устройство → сканировать.
Сессия сразу сохраняется в секрет TG_SESSION (через GH_PAT) и нигде не печатается.
Облачный пароль (если есть) берётся из секрета TG_2FA.
"""
import asyncio, os, subprocess, sys, time
import qrcode
from telethon import TelegramClient, errors
from telethon.sessions import StringSession


def show(url: str) -> None:
    q = qrcode.QRCode(border=2)
    q.add_data(url)
    q.make(fit=True)
    print("\n" + "=" * 60)
    print("Отсканируйте в Телеграме: Настройки → Устройства → Подключить устройство")
    print("Код действует ~30 секунд, потом появится новый.\n")
    q.print_ascii(invert=True)
    sys.stdout.flush()


async def main() -> int:
    client = TelegramClient(StringSession(), int(os.environ["TG_API_ID"]), os.environ["TG_API_HASH"])
    await client.connect()
    qr = await client.qr_login()
    deadline = time.time() + 300
    ok = False
    while time.time() < deadline:
        show(qr.url)
        try:
            await qr.wait(timeout=28)
            ok = True
            break
        except asyncio.TimeoutError:
            await qr.recreate()
        except errors.SessionPasswordNeededError:
            pw = os.environ.get("TG_2FA", "")
            if not pw:
                print("На аккаунте облачный пароль: добавьте секрет TG_2FA и запустите снова.")
                return 1
            await client.sign_in(password=pw)
            ok = True
            break
    if not ok:
        print("Время вышло — запустите workflow ещё раз.")
        return 1
    me = await client.get_me()
    s = client.session.save()
    print(f"::add-mask::{s}")
    subprocess.run(["gh", "secret", "set", "TG_SESSION", "--repo", os.environ["GITHUB_REPOSITORY"]],
                   input=s, text=True, check=True)
    print(f"\n✔ Вход выполнен: {me.first_name} (@{me.username}). Секрет TG_SESSION сохранён.")
    await client.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
