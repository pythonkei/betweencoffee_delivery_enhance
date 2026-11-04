#!/usr/bin/env python3
"""產生首頁「咖啡豆製程」模組（bc-home-service）所需的圖片。

對應模組：templates/betweencoffee_delivery/partials/bc_home_service.html
          static/css/bc-home-service.css / static/js/bc-home-service.js

為什麼要預先產生四種版本（與原站 union-tec.jp 同樣做法）：
  1. hs-N.webp      1920×1080 全幅清晰圖（≥64rem 用；<picture><source>）
  2. hs-N-sp.webp    900×1200 手機直式圖（<img src>，避免手機下載 1920 寬的檔案）
  3. hs-N-blur.webp  480×270 預先高斯模糊（滾動前段與全幅階段疊在最上層，
                     執行期不再跑 filter: blur()，省 GPU）
  4. hs-N-clip.webp  640×444 小膠囊遮罩圖（右上角 320×222 的 clip image）

原始 JPG 不動（static/images/ 下原檔保留），輸出全部寫到
static/images/home-service/。

換圖方式：只改下面 SOURCES 清單（順序 = 第 1~4 張 = 標籤 產地/處理法/烘焙/出爐），
再跑 `python3 scripts/make_hs_images.py`。

原始 JPG 共約 7.1MB（其中一張 5.4MB），依專案規則「大型原始素材不進版控」
已列在 .gitignore（頁面只用產出的 webp）；換素材時把新檔放到 static/images/ 即可。
"""
import os
import sys

from PIL import Image, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "static", "images", "home-service")

# 順序對應左側四個標籤：產地 → 處理法 → 烘焙曲線 → 新鮮出爐
SOURCES = [
    "static/images/diego-catto-9LqctKiRP5c-unsplash.jpg",  # 1 產地（巴西生豆麻布袋）
    "static/images/jolucasru-coffee-8066888.jpg",  # 2 處理法（生豆特寫）
    "static/images/zhxj560-coffee-4512564_1920.jpg",  # 3 烘焙（烘豆機滾筒）
    "static/images/46173-coffee-1044387_1920.jpg",  # 4 出爐（PROBAT 出豆）
]

VARIANTS = [
    # (檔名後綴, 寬, 高, 是否模糊, quality)
    # 全幅版用 1600×900 而非 1920：滿版照片在高熵材質（麻布袋）下 1920 會到 500KB+，
    # 1600 放大到 1440/1920 螢幕肉眼無差，體積少一半。
    ("", 1600, 900, False, 78),
    ("-sp", 900, 1200, False, 78),
    ("-blur", 480, 270, True, 70),
    ("-clip", 640, 444, False, 78),
]


def center_crop(img, tw, th):
    """等比縮放到「剛好蓋滿」目標框後置中裁切（等同 CSS object-fit: cover）。"""
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = max(tw, round(sw * scale)), max(th, round(sh * scale))
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def main():
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    # 模糊半徑跟著輸出尺寸走：480 寬用 10px（放大到全幅後等效 ≈30px）。
    # 2026-10-30 首版用 18px（等效 ≈54px）實測「整片霧掉、看不出是什麼」，
    # 與原站（仍看得出構圖的柔化）差異太大 → 降為 10px。
    blur_radius = 10
    written = 0
    for idx, rel in enumerate(SOURCES, start=1):
        src = os.path.join(BASE_DIR, rel)
        if not os.path.exists(src):
            sys.exit("找不到素材：%s" % src)
        with Image.open(src) as raw:
            base = raw.convert("RGB")
            for suffix, w, h, is_blur, quality in VARIANTS:
                img = center_crop(base, w, h)
                if is_blur:
                    img = img.filter(ImageFilter.GaussianBlur(blur_radius))
                out = os.path.join(OUT_DIR, "hs-%d%s.webp" % (idx, suffix))
                img.save(out, "WEBP", quality=quality, method=6)
                written += 1
                size_kb = round(os.path.getsize(out) / 1024)
                print("%-34s %4dx%-5d %5d KB" % (os.path.basename(out), w, h, size_kb))

    print("\n完成：%d 個檔案 → %s" % (written, OUT_DIR))


if __name__ == "__main__":
    main()
