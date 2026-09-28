#!/usr/bin/env python3
"""
Рендер каруселей 1080x1350 JPG из content/carousels_<неделя>.py через Chromium (Playwright).
Фото: content/photos/<файл>.jpg. Шрифты: FONTS_DIR (fontsource).
Выход: media/<дата>/car_<slug>_NN.jpg (ASCII-пути для Инстаграма).
Запуск: python content/render_carousels.py [--src carousels_2026-09-28.py] [--only slug]
"""
import base64, importlib.util, os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FONTS = Path(os.getenv("FONTS_DIR", "/home/claude/fonts"))
PHOTO_DIR = ROOT / "content" / "photos"
SRC = ROOT / "content" / (sys.argv[sys.argv.index("--src") + 1] if "--src" in sys.argv else "carousels_2026-09-28.py")
# для Телеграма: tg_*.py с POSTS — по одной обложке на пост

sys.path.insert(0, str(Path(__file__).parent))
import brand

PHOTOS = {}  # slug -> (фото обложки, позиция кадра по вертикали), если в карусели не указано "photo"

def b64(p):
    p = Path(p)
    if p.name == brand.AVATAR and not p.exists():  # аватар = кроп из brand.AVATAR_FROM
        from PIL import Image
        src, fx, fy, fr = brand.AVATAR_FROM
        im = Image.open(p.parent / src); w, h = im.size
        cx, cy, r = int(w * fx), int(h * fy), int(w * fr)
        im.crop((cx - r, cy - r, cx + r, cy + r)).resize((300, 300)).save(p, quality=92)
    return base64.b64encode(p.read_bytes()).decode()

def font_css():
    out = []
    for fam, pkg, w, st in [("Oswald", "oswald", 700, "normal"), ("Oswald", "oswald", 500, "normal"),
                            ("Montserrat", "montserrat", 500, "normal"), ("Montserrat", "montserrat", 700, "normal"),
                            ("PT Serif", "pt-serif", 400, "italic")]:
        for sub in ("cyrillic", "latin"):
            f = FONTS / pkg / "files" / f"{pkg}-{sub}-{w}-{st}.woff2"
            out.append(f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:{st};"
                       f"src:url(data:font/woff2;base64,{b64(f)}) format('woff2');}}")
    return "\n".join(out)

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px;overflow:hidden;background:#1d1a17}
.s{position:relative;width:1080px;height:1350px;overflow:hidden;color:#F4ECDF;font-family:Montserrat}
.photo{position:absolute;inset:0;background-size:cover;background-position:center 20%}
.shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.25) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,.35) 50%,rgba(0,0,0,.8) 72%,rgba(0,0,0,.95) 100%)}
.handle{position:absolute;top:56px;left:72px;font:500 26px Montserrat;letter-spacing:.08em;opacity:.85}
.cnt{position:absolute;top:56px;right:72px;font:500 26px Montserrat;opacity:.6}
.label{font:700 26px Montserrat;letter-spacing:.34em;text-transform:uppercase;opacity:.9;margin-bottom:22px}
.h{font-family:Oswald;font-weight:700;text-transform:uppercase;line-height:.98;letter-spacing:.005em}
.serif{font:italic 400 40px 'PT Serif';opacity:.9;margin-top:22px}
.cover .box{position:absolute;left:60px;right:60px;bottom:96px;text-align:center}
.cover .h{font-size:104px}
.swipe{position:absolute;bottom:52px;right:72px;font:500 24px Montserrat;letter-spacing:.2em;text-transform:uppercase;opacity:.7}
.inner{background:#000}
.ava{position:absolute;top:64px;left:72px;display:flex;align-items:center;gap:24px}
.ava i{display:block;width:120px;height:120px;border-radius:50%;background-size:cover;background-position:center 18%;border:3px solid #C9A77C}
.ava b{display:block;font:700 30px Montserrat;color:#F4ECDF}
.ava span{display:block;font:500 24px Montserrat;color:rgba(244,236,223,.6);margin-top:4px}
.inner .box{position:absolute;left:72px;right:72px;top:230px;bottom:150px;display:flex;flex-direction:column;justify-content:center}
.inner .num{font:700 34px Oswald;color:#C9A77C;letter-spacing:.2em;margin-bottom:26px}
.inner .h{font-size:104px;color:#F4ECDF}
.inner .rule{width:120px;height:4px;background:#C9A77C;margin:44px 0 40px}
.inner .t{font:500 46px/1.42 Montserrat;color:rgba(244,236,223,.9)}
.inner .flag{color:#E3B26B;font-size:30px}
.inner .pill{align-self:flex-start;margin-top:56px}
.foot{position:absolute;left:72px;right:72px;bottom:60px;display:flex;justify-content:space-between;font:500 24px Montserrat;opacity:.55;letter-spacing:.05em}
.pill{display:inline-block;margin-top:40px;padding:22px 54px;border:3px solid #F4ECDF;border-radius:80px;font:700 54px Oswald;letter-spacing:.12em}
"""

FIT = """
for (const el of document.querySelectorAll('[data-fit]')) {
  const max = +el.dataset.fit; let fs = parseFloat(getComputedStyle(el).fontSize);
  while (el.scrollHeight > max && fs > 40) { fs -= 2; el.style.fontSize = fs + 'px'; }
}
"""

def esc(s): return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def body_text(t):
    t = esc(t)
    if "[ПРОВЕРИТЬ" in t:
        i = t.index("[ПРОВЕРИТЬ")
        t = t[:i] + f'<br><span class="flag">{t[i:]}</span>'
    return t

def slide_html(c, k, total, photo_cover, photo_ava):
    label, head, text = c["slides"][k]
    handle = f'<div class="handle">{esc(brand.HANDLE)}</div>'
    if k == 0:
        swipe = "" if total == 1 else '<div class="swipe">листайте →</div>'
        return f"""<div class="s cover"><div class="photo" style="background-position:center {c['pos']};background-image:url(data:image/jpeg;base64,{photo_cover})"></div>
<div class="shade"></div>{handle}
<div class="box"><div class="label">{esc(label)}</div><div class="h" data-fit="320">{esc(head)}</div>
<div class="serif">{esc(text)}</div></div>{swipe}</div>"""
    ava = (f'<div class="ava"><i style="background-image:url(data:image/jpeg;base64,{photo_ava})"></i>'
           f'<div><b>{esc(brand.NAME)}</b><span>{esc(brand.ROLE)}</span></div></div>')
    kicker = f"{label}" if not label.isdigit() else f"{label} / {total-2:02d}"
    kicker = f'<div class="num">{esc(kicker).upper()}</div>'
    pill = f'<div class="pill">{esc(c["cta"])}</div>' if k == total - 1 else ""
    swipe = "" if k == total - 1 else "листайте →"
    return f"""<div class="s inner">{ava}<div class="cnt">{k+1}/{total}</div>
<div class="box">{kicker}<div class="h" data-fit="330">{esc(head)}</div><div class="rule"></div>
<div class="t" data-fit="480">{body_text(text)}</div>{pill}</div>
<div class="foot"><span>{esc(brand.HANDLE)}</span><span>{swipe}</span></div></div>"""

def load():
    spec = importlib.util.spec_from_file_location("w", SRC); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m

def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    w = load(); fonts = font_css(); made = []
    if hasattr(w, "POSTS") and not hasattr(w, "CAROUSELS"):
        w.CAROUSELS = [{"date": p["date"], "slug": p["slug"], "photo": p["photo"], "cta": "",
                        "slides": [(p["label"], p["head"], p["sub"])]} for p in w.POSTS]
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page(viewport={"width": 1080, "height": 1350})
        for c in w.CAROUSELS:
            if only and c["slug"] != only: continue
            f0, pos = c.get("photo") or PHOTOS[c["slug"]]
            pc = b64(PHOTO_DIR / f0); pa = b64(PHOTO_DIR / brand.AVATAR); c["pos"] = pos
            out = ROOT / "media" / c["date"]; out.mkdir(parents=True, exist_ok=True)
            n = len(c["slides"])
            for k in range(n):
                html = f"<html><head><meta charset='utf-8'><style>{fonts}{CSS}</style></head><body>{slide_html(c, k, n, pc, pa)}</body></html>"
                pg.set_content(html); pg.evaluate("document.fonts.ready"); pg.evaluate(FIT)
                f = out / f"car_{c['slug']}_{k+1:02d}.jpg"
                pg.screenshot(path=str(f), type="jpeg", quality=92, clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
                made.append(f)
        br.close()
    print(len(made), "слайдов")

if __name__ == "__main__":
    main()
