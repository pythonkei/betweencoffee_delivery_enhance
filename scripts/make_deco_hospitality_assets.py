#!/usr/bin/env python3
"""把高解析 APNG 母檔縮成首頁「社群列尾巴」裝飾用的 96×96 資產。

背景：首頁（partials/bc_brand_stage_hero.html）與 about 頁
（partials/bc_brand_stage.html）的 `.social-item.is-deco` 只顯示 64px，
需要的是一顆 96×96（供視網膜）的 APNG。使用者提供的新版母檔是
1320×1320 / 90 幀 / 4.6 MB，直接掛上去會讓每次載入多抓 4.6 MB，
因此這裡統一由母檔產生小檔。

輸入：static/images/deco_hospitality_static.png（母檔，1320×1320 APNG）
輸出：static/images/deco_hospitality_apng.png      96×96 APNG（一般瀏覽）
      static/images/_deco_hospitality_static.png   96×96 單張（prefers-reduced-motion）

用法：
    python3 scripts/make_deco_hospitality_assets.py
    python3 scripts/make_deco_hospitality_assets.py --size 192 --millis 44
    python3 scripts/make_deco_hospitality_assets.py --master /path/to/new.png
    python3 scripts/make_deco_hospitality_assets.py --no-bump   # 只產檔，不動版號

預設跑完會自動把兩個 partial 的 `?v=` 升到「今天 + 下一個字母」
（WhiteNoise MAX_AGE=1 年，版號沒變瀏覽器就永遠拿舊檔）。
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "static" / "images"
DEFAULT_MASTER = IMG_DIR / "deco_hospitality_static.png"
APNG_OUT = IMG_DIR / "deco_hospitality_apng.png"
STATIC_OUT = IMG_DIR / "_deco_hospitality_static.png"

# 兩處引用這組圖的模板（首頁 hero 版 + about/footer 版）
TEMPLATES = [
    ROOT / "templates" / "betweencoffee_delivery" / "partials" / "bc_brand_stage_hero.html",
    ROOT / "templates" / "betweencoffee_delivery" / "partials" / "bc_brand_stage.html",
]
VERSION_RE = re.compile(
    r"(\{%\s*static\s+'images/_?deco_hospitality_(?:apng|static)\.png'\s*%\}\?v=)"
    r"(\d{8})([a-z])"
)


def kb(path: Path) -> str:
    return "{:.0f}KB".format(path.stat().st_size / 1024)


def collect_versions() -> list:
    """收集兩個 partial 目前用到的版號（去重、排序）。"""
    found = set()
    for tpl in TEMPLATES:
        if not tpl.is_file():
            continue
        for match in VERSION_RE.finditer(tpl.read_text(encoding="utf-8")):
            found.add(match.group(2) + match.group(3))
    return sorted(found)


def next_version() -> str:
    """規則：格式 YYYYMMDDx；同一天多次改就字母往後推，換日從 a 起算。"""
    today = date.today().strftime("%Y%m%d")
    latest = collect_versions()
    same_day = [v for v in latest if v.startswith(today)]
    if not same_day:
        return today + "a"
    letter = max(v[-1] for v in same_day)
    if letter >= "z":
        raise SystemExit("❌ 今天的版號字母已用到 z，請隔天再升版")
    return today + chr(ord(letter) + 1)


def bump_versions(version: str) -> int:
    """把兩個 partial 內的 ?v= 全部換成指定版號，回傳取代次數。"""
    replaced = 0
    for tpl in TEMPLATES:
        if not tpl.is_file():
            print("⚠️  找不到模板：{}".format(tpl))
            continue
        text = tpl.read_text(encoding="utf-8")
        new_text, count = VERSION_RE.subn(lambda m: m.group(1) + version, text)
        if count and new_text != text:
            tpl.write_text(new_text, encoding="utf-8")
        replaced += count
    return replaced



def main() -> int:
    parser = argparse.ArgumentParser(description="縮製首頁 deco_hospitality 資產")
    parser.add_argument("--master", default=str(DEFAULT_MASTER))
    parser.add_argument("--size", type=int, default=96, help="輸出邊長，預設 96（頁面顯示 64px）")
    parser.add_argument(
        "--millis",
        type=int,
        default=33,
        help="每幀毫秒，預設 33（90 幀 ≈ 3.0s，與原設計一致）",
    )
    parser.add_argument("--backup", action="store_true", help="先把現有輸出檔備份成 *_bak")
    parser.add_argument(
        "--no-bump",
        action="store_true",
        help="只產生圖檔，不改 templates 內的 ?v=（除錯用）",
    )
    args = parser.parse_args()

    master = Path(args.master)
    if not master.is_file():
        print("❌ 找不到母檔：{}".format(master))
        return 1

    if args.backup:
        for out in (APNG_OUT, STATIC_OUT):
            if out.is_file():
                bak = out.with_name(out.stem + "_bak" + out.suffix)
                bak.write_bytes(out.read_bytes())
                print("↩︎  備份 {} → {}".format(out.name, bak.name))

    src = Image.open(master)
    n_frames = getattr(src, "n_frames", 1)
    frames = []
    for i in range(n_frames):
        src.seek(i)
        frames.append(src.convert("RGBA").resize((args.size, args.size), Image.LANCZOS))

    frames[0].save(
        APNG_OUT,
        save_all=True,
        append_images=frames[1:],
        duration=args.millis,
        loop=0,
        disposal=1,
        optimize=True,
    )
    frames[0].save(STATIC_OUT, optimize=True)

    check_apng = Image.open(APNG_OUT)
    print("母檔   {}  {}×{} / {} 幀 / {}".format(master.name, src.width, src.height, n_frames, kb(master)))
    print(
        "APNG   {}  {}×{} / {} 幀 / {}ms×{} ≈ {:.1f}s / {}".format(
            APNG_OUT.name,
            check_apng.width,
            check_apng.height,
            getattr(check_apng, "n_frames", 1),
            args.millis,
            n_frames,
            args.millis * n_frames / 1000,
            kb(APNG_OUT),
        )
    )
    print("靜態   {}  {}×{} / {}".format(STATIC_OUT.name, args.size, args.size, kb(STATIC_OUT)))

    if args.no_bump:
        print("\n（--no-bump）未改版號；目前版號：{}".format(", ".join(collect_versions()) or "無"))
        return 0

    version = next_version()
    count = bump_versions(version)
    print(
        "\n✅ 已把 {} 處 `?v=` 升為 {}（bc_brand_stage_hero.html + bc_brand_stage.html）".format(
            count, version
        )
    )
    print("   瀏覽器直接重新整理即可（URL 已變，不需要硬刷新）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
