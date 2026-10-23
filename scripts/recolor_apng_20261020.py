#!/usr/bin/env python3
"""APNG（Animated PNG）換色 / 縮放工具 —— 只依賴 Pillow，不需要 ffmpeg、ImageMagick、apngasm。

為什麼要自己寫：
  * Photoshop / Photopea / GIMP / Krita 都只會讀到 APNG 的第一格，無法把動畫存回 APNG。
  * 線上工具（ezgif 等）多半走 GIF 或重新編碼，容易把 30 fps 改成 10 fps、把 loop 改成播放一次、
    或把 24-bit + alpha 壓成 256 色。
  * Pillow 讀 APNG 時會逐格「合成」好，寫回時可以原封不動帶上「每格毫秒」與 loop，
    所以格數、節奏、循環次數都不會跑掉。

三種改色模式（可合併）：
  1. --line / --fill ：雙色調（duotone）。以每一格的亮度當權重，
                       暗部（黑線稿）→ --line，亮部（白填色）→ --fill，
                       抗鋸齒的中間調自動內插，alpha 完全保留。
                       適合「白填色 + 黑線」這類單色插畫換色。
  2. --hue DEG       ：HSV 色相旋轉（只動有顏色的像素，alpha、明度、飽和度不變）。
                       適合原本就有彩色、只想整體換色系。
  3. --size N        ：等比縮到 N×N（LANCZOS），可順便壓小檔案。

用法範例：
  # 先看原始檔資訊（格數 / 每格毫秒 / loop / 尺寸 / 檔案大小）
  python3 scripts/recolor_apng_20261020.py static/images/deco_hospitality_apng.png --report

  # 線稿改品牌金、填色改純白，輸出 96×96
  python3 scripts/recolor_apng_20261020.py static/images/deco_hospitality_apng.png \
      --line '#c49b63' --fill '#ffffff' --size 96 --out /tmp/deco_gold.png
"""

import argparse
import os
import sys

from PIL import Image, ImageChops

DEFAULT_FALLBACK_MS = 33  # 讀不到每格毫秒時的保險值（約 30 fps）


def parse_hex(value):
    """'#c49b63' / 'c49b63' / '#fff' → (r, g, b)"""
    s = value.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise argparse.ArgumentTypeError("顏色格式要是 #RRGGBB 或 #RGB：%r" % value)
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise argparse.ArgumentTypeError("顏色格式要是 #RRGGBB 或 #RGB：%r" % value)


def load_apng(path):
    """逐格取出「已合成」的 RGBA 影格，並保留每格毫秒與 loop。"""
    with Image.open(path) as im:
        n_frames = getattr(im, "n_frames", 1)
        frames, durations = [], []
        for i in range(n_frames):
            im.seek(i)
            duration = im.info.get("duration")
            try:
                duration = int(round(float(duration)))
            except (TypeError, ValueError):
                duration = DEFAULT_FALLBACK_MS
            if duration <= 0:
                duration = DEFAULT_FALLBACK_MS
            durations.append(duration)
            frames.append(im.convert("RGBA").copy())
        loop = im.info.get("loop", 0)
        try:
            loop = int(loop)
        except (TypeError, ValueError):
            loop = 0
    return frames, durations, loop


def duotone(frame, line_rgb, fill_rgb):
    """亮度 → 兩色內插：暗 = line_rgb、亮 = fill_rgb；alpha 原封不動。"""
    lum = frame.convert("L")
    size = frame.size
    fill_part = ImageChops.multiply(Image.new("RGB", size, fill_rgb), lum.convert("RGB"))
    line_part = ImageChops.multiply(
        Image.new("RGB", size, line_rgb), ImageChops.invert(lum).convert("RGB")
    )
    rgb = ImageChops.add(fill_part, line_part)  # 兩個權重相加恆等於 255，不會溢出
    alpha = frame.getchannel("A")
    return Image.merge("RGBA", (*rgb.split(), alpha))


def hue_shift(frame, degrees):
    """HSV 色相旋轉，保留 alpha。"""
    alpha = frame.getchannel("A")
    hsv = frame.convert("RGB").convert("HSV")
    h, s, v = hsv.split()
    shift = int(round(degrees / 360.0 * 256)) % 256  # Pillow 的 H 是 0..255
    h = h.point(lambda x: (x + shift) % 256)
    rgb = Image.merge("HSV", (h, s, v)).convert("RGB")
    return Image.merge("RGBA", (*rgb.split(), alpha))


def describe(path, frames, durations, loop):
    total_ms = sum(durations)
    unique = sorted(set(durations))
    size_bytes = os.path.getsize(path) if os.path.exists(path) else 0
    w, h = frames[0].size
    print("檔案      : %s" % path)
    print("尺寸      : %d × %d" % (w, h))
    print("格數      : %d" % len(frames))
    print("每格毫秒  : %s%s" % (
        unique if len(unique) <= 6 else "%s … %s" % (unique[:3], unique[-3:]),
        "（單一節奏）" if len(unique) == 1 else "（節奏不一致，已逐格保留）",
    ))
    if total_ms:
        print("平均 fps  : %.2f" % (1000.0 / (total_ms / float(len(durations)))))
    print("總長      : %.2f s" % (total_ms / 1000.0))
    print("loop      : %s" % ("%d（0 = 無限循環）" % loop if loop == 0 else loop))
    print("檔案大小  : %s bytes / %.2f MB" % ("{:,}".format(size_bytes), size_bytes / 1048576.0))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="APNG 換色 / 縮放，保留格數、每格毫秒與 loop（只用 Pillow）"
    )
    ap.add_argument("src", help="來源 APNG（.png）")
    ap.add_argument("--out", help="輸出路徑；不給就只做 --report，不寫檔")
    ap.add_argument("--line", type=parse_hex, metavar="#RRGGBB",
                    help="duotone 的暗部顏色（原作的黑線稿）")
    ap.add_argument("--fill", type=parse_hex, metavar="#RRGGBB",
                    help="duotone 的亮部顏色（原作的白填色）")
    ap.add_argument("--hue", type=float, metavar="DEG",
                    help="HSV 色相旋轉角度（-180 ~ 180）")
    ap.add_argument("--size", type=int, metavar="N",
                    help="等比縮放到 N×N（例如 96、128）")
    ap.add_argument("--report", action="store_true", help="印出來源檔資訊")
    ap.add_argument("--check", action="store_true", help="寫檔後再讀一次，核對格數 / 毫秒 / loop")
    args = ap.parse_args(argv)

    if not os.path.exists(args.src):
        ap.error("找不到檔案：%s" % args.src)
    if not args.out and not args.report:
        ap.error("至少要給 --report 或 --out")
    if (args.line or args.fill) and not (args.line and args.fill):
        ap.error("--line 與 --fill 要一起給（duotone 需要兩端顏色）")
    if not any([args.line, args.hue, args.size, args.out]):
        ap.error("沒有任何要做的轉換（--line/--fill、--hue、--size、--out 至少一個）")

    frames, durations, loop = load_apng(args.src)
    if args.report:
        print("── 來源 ─────────────────────────────")
        describe(args.src, frames, durations, loop)

    if args.out:
        out_frames = []
        for frame in frames:
            new = frame
            if args.hue:
                new = hue_shift(new, args.hue)
            if args.line and args.fill:
                new = duotone(new, args.line, args.fill)
            if args.size:
                new = new.resize((args.size, args.size), Image.LANCZOS)
            out_frames.append(new)

        # 這裡是關鍵：duration 傳「每格毫秒的清單」、loop 原值帶回，動畫節奏不會被改寫。
        out_frames[0].save(
            args.out,
            format="PNG",
            save_all=True,
            append_images=out_frames[1:],
            duration=durations,
            loop=loop,
            optimize=True,
        )

        print("── 輸出 ─────────────────────────────")
        describe(args.out, out_frames, durations, loop)

        if args.check:
            got_frames, got_durations, got_loop = load_apng(args.out)
            problems = []
            if len(got_frames) != len(out_frames):
                problems.append("格數 %d ≠ %d" % (len(got_frames), len(out_frames)))
            if got_durations != durations:
                problems.append("毫秒序列不一致")
            if got_loop != loop:
                problems.append("loop %r ≠ %r" % (got_loop, loop))
            if problems:
                print("✗ 回讀核對失敗：" + "；".join(problems))
                return 1
            print("✓ 回讀核對通過：%d 格 / 總長 %.2f s / loop %d" % (
                len(got_frames), sum(got_durations) / 1000.0, got_loop,
            ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
