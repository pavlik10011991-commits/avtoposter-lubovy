#!/usr/bin/env python3
"""
Автопостер: читает plan.csv и публикует то, у чего подошло время.

Режимы:
  python publisher/publish.py --check            проверить таблицу и медиа, ничего не публиковать
  python publisher/publish.py                    опубликовать всё, у чего наступило время
  python publisher/publish.py --only ID          опубликовать одну строку прямо сейчас (тест)
  python publisher/publish.py --only ID --check  показать, что было бы отправлено

Таблица plan.csv (разделитель «;», UTF-8) — её пишет человек/Claude.
Журнал status.csv — его пишет только скрипт (что и когда вышло, ссылка или ошибка).
Так правки плана и отметки о публикации никогда не конфликтуют.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import html
import json
import os
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "plan.csv"
STATUS = ROOT / "status.csv"
TZ = ZoneInfo(os.getenv("TIMEZONE", "Europe/Moscow"))
MAX_LATE_HOURS = float(os.getenv("MAX_LATE_HOURS", "6"))
IG_API = os.getenv("IG_API_VERSION", "v23.0")
DELIM = ";"

PLAN_COLUMNS = ["id", "дата", "время", "площадка", "формат", "статус", "текст", "медиа", "комментарий"]
STATUS_COLUMNS = ["id", "площадка", "формат", "план", "опубликовано", "результат", "ссылка"]

PLATFORMS = {"telegram": "telegram", "тг": "telegram", "tg": "telegram", "телеграм": "telegram",
             "instagram": "instagram", "ig": "instagram", "инстаграм": "instagram", "инст": "instagram"}
FORMATS = {"пост": "post", "post": "post", "сторис": "story", "story": "story", "stories": "story",
           "карусель": "carousel", "carousel": "carousel", "рилс": "reel", "reel": "reel", "reels": "reel"}
READY = {"готово", "ready", "повторить"}
IMG = {".jpg", ".jpeg", ".png", ".webp"}
VID = {".mp4", ".mov"}


# ───────────────────────── модель ─────────────────────────

@dataclass
class Item:
    id: str
    when: datetime | None
    platform: str
    fmt: str
    approval: str
    text: str
    media: list[Path]
    raw: dict
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        w = self.when.strftime("%d.%m %H:%M") if self.when else "??"
        return f"[{self.id}] {w} {self.platform}/{self.fmt}"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{(k or "").strip(): (v or "") for k, v in r.items()} for r in csv.DictReader(f, delimiter=DELIM)]


def write_status(rows: dict[str, dict]) -> None:
    tmp = STATUS.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=STATUS_COLUMNS, delimiter=DELIM)
        w.writeheader()
        for r in sorted(rows.values(), key=lambda r: (r.get("план", ""), r["id"])):
            w.writerow({k: r.get(k, "") for k in STATUS_COLUMNS})
    tmp.replace(STATUS)


def parse_when(date_s: str, time_s: str) -> datetime:
    date_s, time_s = date_s.strip(), time_s.strip() or "00:00"
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            d = datetime.strptime(date_s, fmt)
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"дата «{date_s}» — нужен формат 2026-09-28 или 28.09.2026")
    try:
        t = datetime.strptime(time_s, "%H:%M")
    except ValueError:
        raise ValueError(f"время «{time_s}» — нужен формат 10:30")
    return d.replace(hour=t.hour, minute=t.minute, tzinfo=TZ)


def load_plan() -> list[Item]:
    rows = read_csv(PLAN)
    if rows:
        missing = [c for c in PLAN_COLUMNS if c not in rows[0]]
        if missing:
            sys.exit(f"В plan.csv нет колонок: {', '.join(missing)}")
    items, seen = [], set()
    for n, r in enumerate(rows, start=2):
        rid = r["id"].strip()
        if not rid and not any(v.strip() for v in r.values()):
            continue  # пустая строка
        it = Item(id=rid or f"строка{n}", when=None,
                  platform=PLATFORMS.get(r["площадка"].strip().lower(), ""),
                  fmt=FORMATS.get(r["формат"].strip().lower(), ""),
                  approval=r["статус"].strip().lower(), text=r["текст"].strip(),
                  media=[ROOT / p.strip() for p in re.split(r"[|\n]", r["медиа"]) if p.strip()], raw=r)
        if not rid:
            it.problems.append(f"строка {n}: пустой id")
        elif rid in seen:
            it.problems.append(f"id «{rid}» повторяется")
        seen.add(rid)
        try:
            it.when = parse_when(r["дата"], r["время"])
        except ValueError as e:
            it.problems.append(str(e))
        if not it.platform:
            it.problems.append(f"площадка «{r['площадка']}» — нужно telegram или instagram")
        if not it.fmt:
            it.problems.append(f"формат «{r['формат']}» — нужно пост / сторис / карусель / рилс")
        validate(it)
        items.append(it)
    return items


# ───────────────────────── проверки ─────────────────────────

def image_size(p: Path):
    try:
        from PIL import Image
        with Image.open(p) as im:
            return im.size
    except Exception:
        return None


def validate(it: Item) -> None:
    P, W = it.problems.append, it.warnings.append
    for m in it.media:
        if not m.exists():
            P(f"нет файла {m.relative_to(ROOT)}")
        elif m.suffix.lower() not in IMG | VID:
            P(f"{m.name}: неподдерживаемый тип файла")
        if it.platform == "instagram" and not m.relative_to(ROOT).as_posix().isascii():
            P(f"{m.name}: для Инстаграма путь к файлу должен быть латиницей")
    imgs = [m for m in it.media if m.suffix.lower() in IMG]
    vids = [m for m in it.media if m.suffix.lower() in VID]
    key = (it.platform, it.fmt)

    if key == ("telegram", "post"):
        if not it.text and not it.media:
            P("пустой пост: нет ни текста, ни медиа")
        if len(it.media) > 10:
            P("в Телеграм-альбоме максимум 10 файлов")
        if len(it.text) > 4096:
            P(f"текст {len(it.text)} символов, лимит Телеграма 4096")
        elif it.media and len(it.text) > 1024:
            W("текст длиннее 1024 — уйдёт отдельным сообщением сразу после медиа")
    elif it.fmt == "story":
        if len(it.media) != 1:
            P("для сторис нужен ровно один файл")
        if it.platform == "telegram" and len(it.text) > 200:
            W("подпись к сторис в ТГ длиннее 200 символов — без Premium её обрежут")
        if it.platform == "instagram" and it.text:
            W("Инстаграм не показывает текст к сторис из API — текст должен быть на картинке")
        for m in imgs:
            s = image_size(m)
            if s and abs(s[0] / s[1] - 9 / 16) > 0.02:
                W(f"{m.name}: {s[0]}×{s[1]}, для сторис лучше 1080×1920")
    elif key == ("instagram", "carousel"):
        if not 2 <= len(it.media) <= 10:
            P("в карусели Инстаграма от 2 до 10 картинок")
        if vids:
            P("в карусели пока поддерживаются только картинки")
        sizes = {image_size(m) for m in imgs}
        if len(sizes) > 1:
            W("картинки карусели разного размера — Инстаграм обрежет по первой")
    elif key == ("telegram", "carousel"):
        P("для Телеграма карусель оформляется как «пост» с несколькими картинками")
    elif it.fmt == "reel":
        if len(vids) != 1 or len(it.media) not in (1, 2):
            P("для рилса нужен один .mp4 (и по желанию обложка .jpg вторым файлом)")
        if it.platform == "telegram":
            W("в Телеграм рилс уйдёт как обычное видео-сообщение")
    elif key == ("instagram", "post"):
        if len(it.media) != 1:
            P("для поста в Инстаграм нужна одна картинка (для нескольких — формат карусель)")
    if it.platform == "instagram":
        if len(it.text) > 2200:
            P(f"подпись {len(it.text)} символов, лимит Инстаграма 2200")
        if it.text.count("#") > 30:
            P("больше 30 хэштегов — Инстаграм отклонит")
        for m in imgs:
            if m.suffix.lower() not in {".jpg", ".jpeg"}:
                P(f"{m.name}: Инстаграм через API принимает только JPG")


# ───────────────────────── Телеграм: бот ─────────────────────────

def md_to_html(text: str) -> str:
    """Безопасное оформление: **жирный**, __курсив__, [текст](ссылка). Всё остальное экранируется."""
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.S)
    t = re.sub(r"__(.+?)__", r"<i>\1</i>", t, flags=re.S)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', t)
    return t


class TelegramBot:
    def __init__(self):
        self.token = env("TG_BOT_TOKEN")
        self.chat = env("TG_CHANNEL")
        self.base = f"https://api.telegram.org/bot{self.token}"

    def call(self, method: str, data: dict, files=None) -> dict:
        r = requests.post(f"{self.base}/{method}", data=data, files=files, timeout=180)
        j = r.json()
        if not j.get("ok"):
            raise RuntimeError(f"Telegram {method}: {j.get('description', r.text)[:300]}")
        return j["result"]

    def link(self, msg_id: int) -> str:
        ch = self.chat
        if ch.startswith("@"):
            return f"https://t.me/{ch[1:]}/{msg_id}"
        if ch.startswith("-100"):
            return f"https://t.me/c/{ch[4:]}/{msg_id}"
        return ""

    def post(self, it: Item) -> str:
        body = md_to_html(it.text)
        base = {"chat_id": self.chat, "parse_mode": "HTML"}
        media = [m for m in it.media if m.suffix.lower() in IMG | VID]
        caption_fits = len(body) <= 1024
        cap = body if caption_fits else ""
        if not media:
            res = self.call("sendMessage", {**base, "text": body})
            return self.link(res["message_id"])
        if len(media) == 1:
            m = media[0]
            kind = "video" if m.suffix.lower() in VID else "photo"
            with m.open("rb") as f:
                res = self.call("sendVideo" if kind == "video" else "sendPhoto",
                                {**base, "caption": cap, **({"supports_streaming": "true"} if kind == "video" else {})},
                                files={kind: f})
            first = res["message_id"]
        else:
            files, group = {}, []
            for i, m in enumerate(media):
                name = f"f{i}"
                files[name] = m.open("rb")
                entry = {"type": "video" if m.suffix.lower() in VID else "photo", "media": f"attach://{name}"}
                if i == 0 and cap:
                    entry |= {"caption": cap, "parse_mode": "HTML"}
                group.append(entry)
            try:
                res = self.call("sendMediaGroup", {"chat_id": self.chat, "media": json.dumps(group)}, files=files)
            finally:
                for f in files.values():
                    f.close()
            first = res[0]["message_id"]
        if not caption_fits:
            self.call("sendMessage", {**base, "text": body})
        return self.link(first)

    def notify(self, text: str) -> None:
        admin = os.getenv("TG_ADMIN_CHAT_ID")
        if admin and self.token:
            try:
                requests.post(f"{self.base}/sendMessage", data={"chat_id": admin, "text": text[:4000]}, timeout=30)
            except Exception:
                pass


# ───────────────────────── Телеграм: сторис канала ─────────────────────────

def tg_story(it: Item) -> str:
    """Сторис в канал публикуется от имени администратора (бот этого не умеет)."""
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.tl import functions, types

    async def run():
        client = TelegramClient(StringSession(env("TG_SESSION")), int(env("TG_API_ID")), env("TG_API_HASH"))
        await client.connect()
        try:
            if not await client.is_user_authorized():
                raise RuntimeError("сессия Телеграма недействительна — заново запустите login_telegram.py")
            peer = await client.get_input_entity(env("TG_CHANNEL"))
            m = it.media[0]
            up = await client.upload_file(str(m))
            if m.suffix.lower() in VID:
                dur, w, h = video_meta(m)
                media = types.InputMediaUploadedDocument(
                    file=up, mime_type="video/mp4",
                    attributes=[types.DocumentAttributeVideo(duration=dur, w=w, h=h, supports_streaming=True)])
            else:
                media = types.InputMediaUploadedPhoto(file=up)
            await client(functions.stories.SendStoryRequest(
                peer=peer, media=media, privacy_rules=[types.InputPrivacyValueAllowAll()],
                caption=it.text[:2048] or None, period=86400))
            return ""
        finally:
            await client.disconnect()

    return asyncio.run(run())


def video_meta(p: Path) -> tuple[float, int, int]:
    import subprocess
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=width,height:format=duration", "-of", "json", str(p)],
                             capture_output=True, text=True, timeout=60).stdout
        j = json.loads(out)
        s = j["streams"][0]
        return float(j["format"]["duration"]), int(s["width"]), int(s["height"])
    except Exception:
        return 15.0, 1080, 1920


# ───────────────────────── Инстаграм ─────────────────────────

class Instagram:
    def __init__(self):
        self.token = env("IG_ACCESS_TOKEN")
        self.user = env("IG_USER_ID")
        self.base = f"https://graph.instagram.com/{IG_API}"

    def url_for(self, p: Path) -> str:
        rel = urllib.parse.quote(p.relative_to(ROOT).as_posix())
        custom = os.getenv("MEDIA_BASE_URL")
        if custom:
            return custom.rstrip("/") + "/" + rel
        repo = env("GITHUB_REPOSITORY")
        ref = os.getenv("GITHUB_REF_NAME", "main")
        return f"https://raw.githubusercontent.com/{repo}/{ref}/{rel}"

    def req(self, method: str, path: str, **params) -> dict:
        params["access_token"] = self.token
        r = requests.request(method, f"{self.base}/{path}", params=params if method == "GET" else None,
                             data=params if method != "GET" else None, timeout=120)
        j = r.json()
        if "error" in j:
            e = j["error"]
            raise RuntimeError(f"Instagram: {e.get('error_user_msg') or e.get('message')} (код {e.get('code')})")
        return j

    def container(self, **params) -> str:
        return self.req("POST", f"{self.user}/media", **params)["id"]

    def video_container(self, video: Path, **params) -> str:
        """Видео грузим напрямую (resumable upload), ссылка не нужна."""
        cid = self.req("POST", f"{self.user}/media", upload_type="resumable", **params)["id"]
        data = video.read_bytes()
        r = requests.post(f"https://rupload.facebook.com/ig-api-upload/{IG_API}/{cid}", data=data, timeout=600,
                          headers={"Authorization": f"OAuth {self.token}", "offset": "0",
                                   "file_size": str(len(data))})
        if r.status_code >= 300:
            raise RuntimeError(f"Instagram загрузка видео: {r.text[:300]}")
        return cid

    def wait(self, cid: str, timeout: int = 600) -> None:
        start = time.time()
        while time.time() - start < timeout:
            st = self.req("GET", cid, fields="status_code,status").get("status_code")
            if st == "FINISHED":
                return
            if st in ("ERROR", "EXPIRED"):
                raise RuntimeError(f"Instagram не смог обработать файл ({st})")
            time.sleep(5)
        raise RuntimeError("Instagram слишком долго обрабатывает файл")

    def publish(self, cid: str) -> str:
        self.wait(cid)
        mid = self.req("POST", f"{self.user}/media_publish", creation_id=cid)["id"]
        try:
            return self.req("GET", mid, fields="permalink").get("permalink", "")
        except Exception:
            return ""

    def post(self, it: Item) -> str:
        imgs = [m for m in it.media if m.suffix.lower() in IMG]
        vids = [m for m in it.media if m.suffix.lower() in VID]
        if it.fmt == "carousel":
            kids = [self.container(image_url=self.url_for(m), is_carousel_item="true") for m in imgs]
            for k in kids:
                self.wait(k)
            return self.publish(self.container(media_type="CAROUSEL", children=",".join(kids), caption=it.text))
        if it.fmt == "reel":
            extra = {"cover_url": self.url_for(imgs[0])} if imgs else {}
            return self.publish(self.video_container(vids[0], media_type="REELS", caption=it.text,
                                                     share_to_feed="true", **extra))
        if it.fmt == "story":
            if vids:
                return self.publish(self.video_container(vids[0], media_type="STORIES"))
            return self.publish(self.container(media_type="STORIES", image_url=self.url_for(imgs[0])))
        return self.publish(self.container(image_url=self.url_for(imgs[0]), caption=it.text))


# ───────────────────────── запуск ─────────────────────────

def env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise RuntimeError(f"не задан секрет {name}")
    return v


def publish_one(it: Item, bot: TelegramBot | None) -> str:
    if it.platform == "telegram":
        return tg_story(it) if it.fmt == "story" else (bot or TelegramBot()).post(it)
    return Instagram().post(it)


def already_done(it: Item, status: dict) -> bool:
    """Опубликованное не повторяем никогда. Ошибку повторяем, только если в плане статус «повторить»."""
    res = status.get(it.id, {}).get("результат", "")
    if not res:
        return False
    if res == "опубликовано":
        return True
    return it.approval != "повторить"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="только проверить, ничего не публиковать")
    ap.add_argument("--only", help="опубликовать одну строку по id прямо сейчас")
    ap.add_argument("--now", help="подменить текущее время (для проверки), формат 2026-09-28T10:00")
    a = ap.parse_args()

    now = datetime.fromisoformat(a.now).replace(tzinfo=TZ) if a.now else datetime.now(TZ)
    items = load_plan()
    status = {r["id"]: r for r in read_csv(STATUS)}

    broken = [it for it in items if it.problems]
    for it in items:
        for w in it.warnings:
            print(f"  ⚠ {it.label}: {w}")
    for it in broken:
        for p in it.problems:
            print(f"  ✖ {it.label}: {p}")

    if a.only:
        due = [it for it in items if it.id == a.only]
        if not due:
            print(f"Строки с id «{a.only}» нет в plan.csv")
            return 1
    else:
        due = [it for it in items if it.approval in READY and it.when and it.when <= now
               and not already_done(it, status)]

    if a.check:
        upcoming = sorted((it for it in items if it.when and it.when > now and it.approval in READY),
                          key=lambda i: i.when)
        print(f"\nСейчас {now:%d.%m.%Y %H:%M} ({TZ.key}). Строк в плане: {len(items)}, "
              f"с ошибками: {len(broken)}.")
        print(f"К публикации прямо сейчас: {len(due)}")
        for it in due:
            print(f"  → {it.label}  файлов: {len(it.media)}  текст: {len(it.text)} симв.")
        print(f"Дальше по расписанию: {len(upcoming)}")
        for it in upcoming[:15]:
            print(f"    {it.label}")
        drafts = sum(1 for it in items if it.approval not in READY | {"пропустить"})
        if drafts:
            print(f"Черновиков (не выйдут, пока статус не «готово»): {drafts}")
        return 1 if broken else 0

    bot = None
    try:
        bot = TelegramBot()
    except RuntimeError:
        pass

    ok = fail = 0
    for it in sorted(due, key=lambda i: i.when or now):
        rec = {"id": it.id, "площадка": it.platform, "формат": it.fmt,
               "план": it.when.strftime("%Y-%m-%d %H:%M") if it.when else "",
               "опубликовано": now.strftime("%Y-%m-%d %H:%M")}
        late = (now - it.when) if it.when else timedelta(0)
        if it.problems:
            rec["результат"] = "ошибка: " + "; ".join(it.problems)
        elif not a.only and late > timedelta(hours=MAX_LATE_HOURS):
            rec["результат"] = f"пропущено: опоздание {late.total_seconds() / 3600:.1f} ч"
        else:
            try:
                rec["ссылка"] = publish_one(it, bot)
                rec["результат"] = "опубликовано"
                rec["опубликовано"] = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
            except Exception as e:
                rec["результат"] = f"ошибка: {e}"
        status[it.id] = rec
        write_status(status)  # сохраняем после каждой публикации
        good = rec["результат"] == "опубликовано"
        ok += good
        fail += not good
        print(("✔ " if good else "✖ ") + f"{it.label}: {rec['результат']} {rec.get('ссылка', '')}")
        if not good and bot:
            bot.notify(f"⚠️ Автопостер: {it.label}\n{rec['результат']}")

    if not due:
        print(f"{now:%d.%m %H:%M}: публиковать нечего")
    return 1 if fail and not ok else 0


if __name__ == "__main__":
    sys.exit(main())
