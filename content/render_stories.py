#!/usr/bin/env python3
"""Сторис 1080x1920 JPG из content/stories_<неделя>.py. Выход: media/<дата>/story_1_wish.jpg, story_2_topic.jpg"""
import importlib.util, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
from render_carousels import font_css, b64, esc, FIT, PHOTO_DIR, ROOT
import brand

SRC = ROOT / "content" / (sys.argv[sys.argv.index("--src") + 1] if "--src" in sys.argv else "stories_2026-09-28.py")

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#000}
.s{position:relative;width:1080px;height:1920px;overflow:hidden;color:#F4ECDF;font-family:Montserrat}
.photo{position:absolute;inset:0;background-size:cover}
.shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 16%,rgba(0,0,0,.05) 36%,rgba(0,0,0,.72) 52%,rgba(0,0,0,.9) 68%,rgba(0,0,0,.96) 100%)}
.handle{position:absolute;top:150px;left:0;right:0;text-align:center;font:500 30px Montserrat;letter-spacing:.1em;opacity:.85}
.box{position:absolute;left:80px;right:80px;bottom:300px;text-align:center}
.label{font:700 30px Montserrat;letter-spacing:.34em;text-transform:uppercase;margin-bottom:28px;color:#E6C9A0}
.h{font-family:Oswald;font-weight:700;text-transform:uppercase;line-height:1;font-size:108px}
.serif{font:italic 400 50px/1.3 'PT Serif';margin-top:32px;opacity:.95}
.num{position:absolute;top:330px;left:0;right:0;text-align:center;font:italic 400 64px "PT Serif";color:#E6C9A0;opacity:.0}
.nophoto .box{bottom:auto;top:52%;transform:translateY(-50%)}
.nophoto .h{line-height:1.08}
.pill{display:inline-block;margin-top:48px;padding:22px 50px;border:3px solid #F4ECDF;border-radius:80px;font:700 36px Montserrat;letter-spacing:.08em}
"""

PILL = "СЕГОДНЯ В 19:00"

def story(photo, pos, label, head, sub, topic):
    pill = f'<div class="pill">{PILL}</div>' if topic else ""
    if topic:
        sub = sub.replace(" · сегодня в 19:00", "").replace("сегодня в 19:00", "").replace(" · разбор в 19:00", "").strip(" ·")
    serif = f'<div class="serif">{esc(sub)}</div>' if sub else ""
    if photo:
        bp = pos if " " in pos else "center " + pos
        bg = f'<div class="photo" style="background-position:{bp};background-image:url(data:image/jpeg;base64,{b64(PHOTO_DIR / photo)})"></div><div class="shade"></div>'
    else:  # без фото: фирменный фон (pos = цвет акцента)
        bg = f'<div class="photo" style="background:radial-gradient(120% 70% at 50% 0%,{pos} 0%,#2A211C 55%,#14100E 100%)"></div><div class="num">{esc(label)}</div>'
    cls = "s" if photo else "s nophoto"
    return f"""<div class="{cls}">{bg}<div class="handle">{esc(brand.HANDLE)}</div>
<div class="box"><div class="label">{esc(label)}</div><div class="h" data-fit="{400 if topic else 380}">{esc(head)}</div>
{serif}{pill}</div></div>"""

def main():
    spec = importlib.util.spec_from_file_location("s", SRC); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    fonts = font_css(); n = 0
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page(viewport={"width": 1080, "height": 1920})
        for d in m.DAYS:
            global PILL; PILL = d.get("pill", "СЕГОДНЯ В 19:00")
            out = ROOT / "media" / d["date"]; out.mkdir(parents=True, exist_ok=True)
            pref = d.get("prefix", "story")
            items = [(f"{pref}_{i+1}", st["text"], st["photo"], st.get("pill", False)) for i, st in enumerate(d["stories"])] if "stories" in d else \
                    [("story_1_wish", d["wish"], d["wish_photo"], False), ("story_2_topic", d["topic"], d["topic_photo"], True)]
            for name, text, photo, topic in items:
                d.setdefault(name, None)
                pg.set_content(f"<html><head><meta charset='utf-8'><style>{fonts}{CSS}</style></head><body>{story(*photo, *text, topic)}</body></html>")
                pg.evaluate("document.fonts.ready"); pg.evaluate(FIT)
                pg.screenshot(path=str(out / f"{name}.jpg"), type="jpeg", quality=92, clip={"x": 0, "y": 0, "width": 1080, "height": 1920}); n += 1
        br.close()
    print(n, "сторис")

if __name__ == "__main__":
    main()
