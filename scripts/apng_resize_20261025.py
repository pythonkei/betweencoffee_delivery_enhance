#!/usr/bin/env python3
"""APNG 縮放／轉存工具（自帶 APNG 解碼器）—— 只依賴 Pillow。

為什麼不直接用 Pillow 的 im.seek()：
  首頁「推薦頁面」用的 static/images/ani_bean_apng.png 是 **Adam7 交錯**（IHDR
  interlace=1）的 APNG，Pillow 10.x 解第 2 格以後會炸
  `TypeError: function takes at most 3 arguments (4 given)`
  （APNG 差分格 + 交錯時把 disposal/blend 多餘參數丟給 zip 解碼器）。
  這裡改成自己依 PNG chunk 逐格解：
    · 每一格的 fdAT（或第一格的 IDAT）本身是一段「完整的 PNG 影像資料流」，
      把它組回一張獨立 PNG（IHDR 用該格 fcTL 的 bbox 尺寸），Pillow 就能正常
      解交錯圖，再依 fcTL 的 blend / dispose 疊回畫布。
  好處：交錯／非交錯、有大有小、差分格的來源都能吃，而且不需要 ffmpeg、
  ImageMagick、apngasm、apngdis。

用法：
  # 看來源資訊（尺寸 / 格數 / 每格毫秒 / loop）
  python3 scripts/apng_resize_20261025.py static/images/ani_coffee_apng.png --report

  # 縮成 332×332 的 APNG（保留格數、每格毫秒與 loop）
  python3 scripts/apng_resize_20261025.py static/images/ani_coffee_apng.png \\
      --size 332 --out static/images/recommended-pages/clip-coffee-ani.png --check
"""

import argparse
import io
import os
import struct
import sys
import zlib

from PIL import Image

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _chunks(path):
    """回傳 (檔案內容, [(type, data_offset, length)])。"""
    with open(path, "rb") as fh:
        data = fh.read()
    if not data.startswith(PNG_SIG):
        raise SystemExit("不是 PNG：%s" % path)
    out, off = [], 8
    while off + 8 <= len(data):
        (length,) = struct.unpack(">I", data[off:off + 4])
        ctype = data[off + 4:off + 8].decode("latin-1")
        out.append((ctype, off + 8, length))
        off += 12 + length
        if ctype == "IEND":
            break
    return data, out


def _pack(ctype, payload):
    return (struct.pack(">I", len(payload)) + ctype + payload
            + struct.pack(">I", zlib.crc32(ctype + payload) & 0xFFFFFFFF))


def decode_apng(path):
    """逐格解出「已合成」的 RGBA 影格，同時保留每格毫秒與 loop。

    回傳 (frames, durations_ms, loop, (W, H))。
    """
    data, chunks = _chunks(path)
    ihdr = None
    loop = 0
    frames_meta = []          # [(control_dict, [payload_bytes, ...])]
    for ctype, off, length in chunks:
        payload = data[off:off + length]
        if ctype == "IHDR":
            ihdr = payload
        elif ctype == "acTL":
            loop = struct.unpack(">I", payload[4:8])[0]
        elif ctype == "fcTL":
            seq, w, h, x, y, dn, dd, dispose, blend = struct.unpack(
                ">IIIIIHHBB", payload[:26])
            frames_meta.append(({"seq": seq, "w": w, "h": h, "x": x, "y": y,
                                 "dn": dn, "dd": dd, "dispose": dispose,
                                 "blend": blend}, []))
        elif ctype == "IDAT" and frames_meta:      # 第一格的影像資料
            frames_meta[0][1].append(payload)
        elif ctype == "fdAT" and frames_meta:      # 之後各格（前 4 bytes 是序號）
            frames_meta[-1][1].append(payload[4:])
    if not ihdr or not frames_meta:
        raise SystemExit("不是 APNG（缺少 acTL/fcTL）：%s" % path)

    width, height = struct.unpack(">II", ihdr[:8])
    bit_depth, color_type = ihdr[8], ihdr[9]
    comp, filt, interlace = ihdr[10], ihdr[11], ihdr[12]

    def decode_tile(meta, payload):
        """把某一格自己的資料流組成獨立 PNG 後解碼（Pillow 支援 Adam7）。"""
        ihdr_tile = struct.pack(">IIBBBBB", meta["w"], meta["h"], bit_depth,
                                color_type, comp, filt, interlace)
        png = (PNG_SIG + _pack(b"IHDR", ihdr_tile)
               + _pack(b"IDAT", b"".join(payload)) + _pack(b"IEND", b""))
        with Image.open(io.BytesIO(png)) as im:
            return im.convert("RGBA")

    frames, durations = [], []
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for meta, payload in frames_meta:
        before = canvas.copy() if meta["dispose"] == 2 else None
        tile = decode_tile(meta, payload)
        if meta["blend"] == 0:                     # SOURCE：連 alpha 一起覆蓋
            canvas.paste(tile, (meta["x"], meta["y"]))
        else:                                      # OVER：alpha 合成
            canvas.alpha_composite(tile, dest=(meta["x"], meta["y"]))
        frames.append(canvas.copy())
        den = meta["dd"] or 100
        durations.append(max(1, int(round(meta["dn"] * 1000.0 / den))))
        if meta["dispose"] == 1:                   # BACKGROUND：清空該格區域
            canvas.paste((0, 0, 0, 0), (meta["x"], meta["y"],
                                        meta["x"] + meta["w"],
                                        meta["y"] + meta["h"]))
        elif meta["dispose"] == 2 and before is not None:
            canvas = before
    return frames, durations, loop, (width, height)


def report(label, path, frames, durations, loop):
    size_bytes = os.path.getsize(path)
    unique = sorted(set(durations))
    total_ms = sum(durations)
    print("── %s ─────────────────────────────" % label)
    print("路徑      : %s" % path)
    print("尺寸      : %d×%d" % frames[0].size)
    print("格數      : %d" % len(frames))
    print("每格毫秒  : %s %s" % (
        unique if len(unique) <= 6 else "%s … %s" % (unique[:3], unique[-3:]),
        "（單一節奏）" if len(unique) == 1 else "（節奏不一致，已逐格保留）"))
    print("總長      : %.2f s" % (total_ms / 1000.0))
    if total_ms:
        print("平均 fps  : %.2f" % (1000.0 * len(durations) / total_ms))
    print("loop      : %s" % ("%d（0 = 無限循環）" % loop if loop == 0 else loop))
    print("檔案大小  : %s bytes / %.2f MB" % (
        "{:,}".format(size_bytes), size_bytes / 1048576.0))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="APNG 縮放（保留格數 / 每格毫秒 / loop，支援 Adam7 交錯來源）")
    ap.add_argument("src", help="來源 APNG（.png）")
    ap.add_argument("--out", help="輸出 APNG 路徑；不給就只做 --report")
    ap.add_argument("--size", type=int, metavar="N",
                    help="等比縮成 N×N（LANCZOS）")
    ap.add_argument("--report", action="store_true", help="印出來源資訊")
    ap.add_argument("--check", action="store_true",
                    help="寫檔後回讀，核對格數 / 毫秒 / loop")
    args = ap.parse_args(argv)

    if not os.path.exists(args.src):
        ap.error("找不到檔案：%s" % args.src)
    if not args.out and not args.report:
        ap.error("至少要給 --report 或 --out")

    frames, durations, loop, src_size = decode_apng(args.src)
    if args.report:
        report("來源（%d×%d）" % src_size, args.src, frames, durations, loop)

    if not args.out:
        return 0

    out_frames = frames
    if args.size:
        out_frames = [f.resize((args.size, args.size), Image.LANCZOS)
                      for f in frames]

    out_frames[0].save(args.out, format="PNG", save_all=True,
                       append_images=out_frames[1:], duration=durations,
                       loop=loop, optimize=True)
    report("輸出", args.out, out_frames, durations, loop)

    if args.check:
        got_frames, got_durations, got_loop, _ = decode_apng(args.out)
        problems = []
        # Pillow 寫 APNG 時會把「與前一格完全相同」的影格合併成一格並累加毫秒
        # （畫面不變、總長不變），所以這裡只驗：總長一致、格數不增加、loop、尺寸。
        if sum(got_durations) != sum(durations):
            problems.append("總長 %d ms ≠ %d ms"
                            % (sum(got_durations), sum(durations)))
        if len(got_frames) > len(out_frames):
            problems.append("格數 %d > %d" % (len(got_frames), len(out_frames)))
        if got_loop != loop:
            problems.append("loop %r ≠ %r" % (got_loop, loop))
        if got_frames[0].size != out_frames[0].size:
            problems.append(
                "尺寸 %s ≠ %s" % (got_frames[0].size, out_frames[0].size))
        if problems:
            print("✗ 回讀核對失敗：" + "；".join(problems))
            return 1
        merged = len(out_frames) - len(got_frames)
        print("✓ 回讀核對通過：%d 格 / %d×%d / 總長 %.2f s / loop %d%s" % (
            len(got_frames), got_frames[0].size[0], got_frames[0].size[1],
            sum(got_durations) / 1000.0, got_loop,
            "（Pillow 合併了 %d 個與前一格相同的影格，總長不變）" % merged
            if merged else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
