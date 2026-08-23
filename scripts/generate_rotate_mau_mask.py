#!/usr/bin/env python3
"""
generate_rotate_mau_mask.py — Between Coffee about.html rotate-mau 圓形文字 mask 產生器

把文字沿圓形路徑排列，輸出 SVG mask 的 data URI（供 bc-rotate-mau.css 使用）。

用法:
  python scripts/generate_rotate_mau_mask.py --text "Taste Right Taste Time" --output /tmp/mask.txt

參數:
  --text         要顯示的文字（沿圓周排列）
  --scale-factor 字尺寸縮放（預設 0.85 = 縮小 15%）
  --span-degree  文字環角度跨度（預設 300°；360=繞滿，<360=字距更緊但有缺口）
  --radius       圓周半徑（預設 355，字元基線所在）
  --font         Mogra 字型檔路徑（預設 ~/Downloads/Mogra.zip 解壓）

字距控制:
  span-degree 越小 → 字元間距越緊（間隙越小），但圓周會有缺口。

產出: data URI 字串寫入 --output 檔案，貼到 bc-rotate-mau.css 的
  -webkit-mask-image: <URI>;
"""
import argparse
import math
import os
import re
import subprocess
import tempfile
import urllib.parse
import zipfile

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

FONT_ZIP = os.path.expanduser("~/Downloads/Mogra.zip")
FONT_TTF = os.path.expanduser("~/.cache/bc-rotate-mau/Mogra-Regular.ttf")


def ensure_font():
    """確保 Mogra 字型可用（從 zip 解壓一次到快取）。"""
    if os.path.exists(FONT_TTF):
        return FONT_TTF
    os.makedirs(os.path.dirname(FONT_TTF), exist_ok=True)
    if os.path.exists(FONT_ZIP):
        with zipfile.ZipFile(FONT_ZIP) as zf:
            for name in zf.namelist():
                if name.lower().endswith(".ttf"):
                    with zf.open(name) as src, open(FONT_TTF, "wb") as dst:
                        dst.write(src.read())
                    return FONT_TTF
    raise SystemExit(f"找不到 Mogra 字型（{FONT_ZIP}）")


def generate(text, scale_factor, span_degree, radius, font_path, font_size=None, gap=40, tight_gap=6):
    font = TTFont(font_path)
    upem = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    glyphSet = font.getGlyphSet()
    asc = font["hhea"].ascent

    # 收集每個字元的 path + ink 資訊（字形實際寬，不含 advance 留白）
    chars = []  # (ch, gid, d, ink_w, xmin, step)
    for ch in text:
        gid = cmap.get(ord(ch))
        if gid is None:
            print(f"  ⚠️ 缺字形: {ch!r}（以空格代替）")
            chars.append((ch, None, None, 0, 0, 300))  # 空格用固定步長
            continue
        pen = SVGPathPen(glyphSet)
        glyphSet[gid].draw(pen)
        d = pen.getCommands()
        # 從 path 數字算 ink 寬（minX, maxX）
        nums = [float(x) for x in re.findall(r"[-+]?[0-9]*\.?[0-9]+", d)]
        xs = nums[0::2]
        xmin = min(xs) if xs else 0
        xmax = max(xs) if xs else 0
        ink_w = xmax - xmin if xs else 0
        if ch == " ":  # 空格：用較大步長，不疊加 gap 的間隙
            chars.append((ch, gid, d, 0, 0, 300))
        else:
            chars.append((ch, gid, d, ink_w, xmin, ink_w + gap))

    # 視覺間隙收緊：T/R（寬字元右側下半部內凹）後接 i 時，視覺空洞明顯
    # → 縮短前一字元（T/R）的步長（間隙 tight_gap，比 gap 小）
    prev_ns = None
    prev_idx = -1
    for idx, c in enumerate(chars):
        ch = c[0]
        if ch == " " or c[1] is None:
            prev_ns = None
            prev_idx = -1
            continue
        if prev_ns in ("T", "R") and ch == "i" and prev_idx >= 0:
            old = chars[prev_idx]
            chars[prev_idx] = (old[0], old[1], old[2], old[3], old[4], old[3] + tight_gap)
        prev_ns = ch
        prev_idx = idx

    total_step = sum(c[5] for c in chars)

    # 字尺寸（核心：scale 必須匹配步長，否則 ink 弧長≠步長弧長 → 字元重疊）
    #   scale = 2πR / total_step（讓字元 ink 弧長 = 步長弧長，間隙統一）
    #   --font-size 給定時反推 R；否則用 --radius
    if font_size:
        s = font_size / asc
        R = s * total_step / (2 * math.pi)
    else:
        R = radius
        s = 2 * math.pi * R / total_step
    cap_h = asc * s
    print(f"字高 ≈ {cap_h:.0f}px，R={R:.0f}，外緣 ≈ {R + cap_h:.0f}（須 ≤500）")

    start_angle = -span_degree / 2  # 對稱，缺口在底部
    paths = []
    cum = 0.0
    for ch, gid, d, ink_w, xmin, step in chars:
        if gid is None:
            cum += step
            continue
        # 字元 ink 中心（相對 glyph origin）= xmin + ink_w/2
        # path transform 平移 -center*s，讓 ink 中心對齊到角度位置（θ 點）
        center = xmin + ink_w / 2
        frac = (cum + ink_w / 2) / total_step
        theta = start_angle + span_degree * frac
        paths.append(
            f'<g transform="translate(500 500) rotate({theta:.2f}) translate(0 {-R})">'
            f'<path transform="translate({-center * s:.2f} 0) scale({s} {-s})" d="{d}"/></g>'
        )
        cum += step

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">'
        + "".join(paths)
        + "</svg>"
    )
    return 'url("data:image/svg+xml;charset=utf-8,' + urllib.parse.quote(svg) + '")'


def main():
    p = argparse.ArgumentParser(description="rotate-mau 圓形文字 mask 產生器")
    p.add_argument("--text", default="Taste Right Taste Time", help="要顯示的文字")
    p.add_argument("--scale-factor", type=float, default=0.85, help="字尺寸縮放（0.85=縮小15%）")
    p.add_argument("--font-size", type=float, default=None,
                   help="目標字高 px（直接指定，優先於 --scale-factor；如 77）")
    p.add_argument("--span-degree", type=float, default=300, help="文字環角度跨度（<360=字距更緊）")
    p.add_argument("--radius", type=float, default=355, help="圓周半徑")
    p.add_argument("--output", default="/tmp/rotate_mau_mask.txt", help="輸出檔")
    p.add_argument("--font", default=None,
                   help="字型 TTF/OTF 路徑（預設用 Mogra；可指定其他字型如 Playfair）")
    p.add_argument("--gap", type=float, default=40,
                   help="字元間統一間隙（upem 單位，預設 40；越大字距越鬆）")
    p.add_argument("--tight-gap", type=float, default=6,
                   help="T/R 後接 i 的收緊間隙（upem，預設 6；比 gap 小則 Ti/Ri 更緊）")
    args = p.parse_args()

    font = ensure_font() if not args.font else os.path.expanduser(args.font)
    uri = generate(args.text, args.scale_factor, args.span_degree, args.radius, font, args.font_size, args.gap, args.tight_gap)
    with open(args.output, "w") as f:
        f.write(uri + "\n")
    print(f"✅ mask 已寫入 {args.output}（{len(uri)} bytes）")
    print(f"   字距: span={args.span_degree}°  |  尺寸: ×{args.scale_factor}"
          + (f"（字高 {args.font_size}px）" if args.font_size else ""))


if __name__ == "__main__":
    main()
