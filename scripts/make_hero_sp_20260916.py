#!/usr/bin/env python3
"""產生 GUNTE hero 手機端直式 sp 圖檔（3:4，510×680，對齊原站 hero-slideNN-photo-sp@2x.jpg 規格）

背景：
  原站手機端是另一份直式檔（510×680 = 3:4），所以 .hero_slide_item_img 是長方形；
  本專案 7 張 slide 的 .vis-sp 與 .hide-sp 指向同一張「正方形」檔（1080/660/630/720），
  而 base.html 全域 responsive-system.css 有 `img { max-height:100%; height:auto }`
  → 高度改由圖檔真實比例決定 → 手機端渲染成 255×255 正方形（與原站不符）。

  本腳本把正方形原圖「置中裁切 3:4」（保留全高、切掉左右）再輸出 510×680 WebP，
  換掉模板的 vis-sp src 即可（CSS 不需 object-fit）。

用法：
  python3 scripts/make_hero_sp_20260916.py                 # dry-run：只報告與輸出對照拼圖
  python3 scripts/make_hero_sp_20260916.py --apply         # 實際寫入 static/images/
  python3 scripts/make_hero_sp_20260916.py --offset 0,0,0.15,0,0,0,0 --apply   # 逐張水平偏移（1~7）
    offset 正值＝裁切框往右移（-0.5~0.5，0＝置中）

輸出：
  static/images/NN_sp_510x680.webp（NN = 01..07）
  /tmp/hero_sp_preview.png（原圖切點 + 裁切結果對照，供目視確認主體未被切到）
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

PROJ = "/home/kei/Desktop/betweencoffee_delivery_enhance"
IMG_DIR = os.path.join(PROJ, "static/images")
PREVIEW = "/tmp/hero_sp_preview.png"

APPLY = "--apply" in sys.argv
OFFSETS = [0.0] * 7
if "--offset" in sys.argv:
    raw = sys.argv[sys.argv.index("--offset") + 1]
    vals = [float(v) for v in raw.split(",")]
    if len(vals) == 1:
        vals = vals * 7
    assert len(vals) == 7, "--offset 需 1 個或 7 個逗號分隔數值"
    OFFSETS = [max(-0.5, min(0.5, v)) for v in vals]

# slide 編號 → 來源檔（皆正方形）
SOURCES = [
    (1, "01_1080.webp"),
    (2, "02_1080.webp"),
    (3, "03_1080.webp"),
    (4, "04_660.webp"),
    (5, "05_630.webp"),
    (6, "06_720.jpg"),
    (7, "07_1080.jpg"),
]

TARGET = (510, 680)  # 3:4，原站 -sp@2x 規格
RATIO = TARGET[0] / TARGET[1]  # 0.75


def crop_box(w, h, offset):
    """置中（可水平偏移）裁切出 3:4 區域，回傳 (x0, y0, x1, y1)。"""
    cw, ch = w, round(w / RATIO)
    if ch > h:  # 來源偏寬 → 改以高度為準
        ch, cw = h, round(h * RATIO)
    x0 = round((w - cw) * (0.5 + offset))
    x0 = max(0, min(w - cw, x0))
    y0 = round((h - ch) * 0.5)
    return x0, y0, x0 + cw, y0 + ch


def main():
    rows = []
    for (idx, name), offset in zip(SOURCES, OFFSETS):
        src = os.path.join(IMG_DIR, name)
        if not os.path.exists(src):
            print(f"✗ 缺少來源檔：{src}")
            sys.exit(1)
        im = Image.open(src).convert("RGB")
        w, h = im.size
        box = crop_box(w, h, offset)
        crop = im.crop(box).resize(TARGET, Image.LANCZOS)
        out = os.path.join(IMG_DIR, f"{idx:02d}_sp_510x680.webp")
        drop_w = round((w - (box[2] - box[0])) / w * 100)
        print(
            f"slide {idx}: {name} {w}×{h} → 裁切 {box[2]-box[0]}×{box[3]-box[1]} (x0={box[0]}, 切掉左右共 {drop_w}%)"
            f" → {os.path.basename(out)} {TARGET[0]}×{TARGET[1]} offset={offset:+.2f}"
        )
        if APPLY:
            crop.save(out, "WEBP", quality=82, method=6)
            print(f"    ✔ 已寫入 {out} ({os.path.getsize(out) // 1024} KB)")
        rows.append((idx, name, im, box, crop))

    # 對照拼圖：左＝原圖（切點外圍壓暗）、右＝裁切結果
    TH = 200
    SW = round(TH * 1.0)
    CW = round(TH * RATIO)
    pad = 12
    sheet_w = SW + CW + pad * 3 + 210
    sheet = Image.new("RGB", (sheet_w, (TH + pad) * len(rows) + pad), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except Exception:
        font = ImageFont.load_default()
    for i, (idx, name, im, box, crop) in enumerate(rows):
        y = pad + i * (TH + pad)
        thumb = im.resize((SW, SW), Image.LANCZOS)
        tdraw = ImageDraw.Draw(thumb, "RGBA")
        tdraw.rectangle([0, 0, box[0] * SW / im.width, SW], fill=(0, 0, 0, 165))
        tdraw.rectangle([box[2] * SW / im.width, 0, SW, SW], fill=(0, 0, 0, 165))
        tdraw.rectangle(
            [box[0] * SW / im.width, 0, box[2] * SW / im.width, SW], outline=(255, 210, 90, 255), width=2
        )
        sheet.paste(thumb, (pad, y))
        sheet.paste(crop.resize((CW, TH), Image.LANCZOS), (pad * 2 + SW, y))
        draw.text((pad * 3 + SW + CW, y + TH // 2 - 10), f"{idx:02d}  {name}", fill=(230, 230, 230), font=font)
        draw.text((pad * 3 + SW + CW, y + TH // 2 + 10), f"→ {idx:02d}_sp_510x680.webp", fill=(150, 200, 255), font=font)
    sheet.save(PREVIEW)
    print(f"\n對照拼圖：{PREVIEW}（左＝原圖與切點，右＝裁切結果）")
    print("dry-run：未寫入檔案（加 --apply 才寫入）" if not APPLY else "\n✅ 已全部寫入")


if __name__ == "__main__":
    main()
