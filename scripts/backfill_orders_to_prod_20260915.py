#!/usr/bin/env python3
"""回補本地 → 正式（Supabase）訂單與帳號（2026-09-15 最終版）

A. 以 Django 模型為權威，對齊正式庫 eshop_ordermodel 的 varchar 寬度
B. 帳號：略過 username/email 已存在者（fb_kei 併入既有帳號），其餘建立為降權+停用
C. 訂單：user_id remap；unique 欄位（order_number/pickup_code）撞號與超長值自動改派
D. 佇列：只補屬於新訂單的列（unique 撞號者略過）
E. setval 修正 sequence；全程單一 transaction，任何錯誤 rollback
用法： python3 /tmp/bc_backfill6.py [--apply]
"""

import os
import re
import sys

import django
import psycopg2
from psycopg2.extras import Json, execute_values

APPLY = "--apply" in sys.argv
PROJ = "/home/kei/Desktop/betweencoffee_delivery_enhance"
sys.path.insert(0, PROJ)
ENV = PROJ + "/.env"

USER_REMAP = {58: 62}
FORCE_FLAGS = {"is_superuser": False, "is_staff": False, "is_active": False}

line = next(l for l in open(ENV, encoding="utf-8").read().split("\n") if "DATABASE_URL=" in l and "pooler" in l)
pu, pp, ph, pport, _ = re.search(r"DATABASE_URL=postgresql://([^:]+):([^@]+)@([^:/]+):(\d+)/(\S*)", line).groups()
prod = psycopg2.connect(host=ph, port=int(pport), user=pu, password=pp, dbname="postgres",
                        sslmode="require", connect_timeout=20)
local = psycopg2.connect(host="127.0.0.1", port=5432, user="postgres", password="postgres",
                         dbname="betweencoffee_delivery_db", connect_timeout=10)


def q(c, sql, a=None):
    cur = c.cursor()
    cur.execute(sql, a)
    return cur.fetchall()


def pk_cols(c, t):
    return [r[0] for r in q(c, """select a.attname from pg_index i
        join pg_attribute a on a.attrelid=i.indrelid and a.attnum=any(i.indkey)
        where i.indrelid=%s::regclass and i.indisprimary order by a.attnum""", ("public." + t,))]


def uq_cols(c, t):
    return [r[0] for r in q(c, """select a.attname from pg_index i
        join pg_attribute a on a.attrelid=i.indrelid and a.attnum=any(i.indkey)
        where i.indrelid=%s::regclass and i.indisunique and not i.indisprimary
          and array_length(i.indkey,1)=1""", ("public." + t,))]


def cols(c, t):
    return [r[0] for r in q(c, """select column_name from information_schema.columns
        where table_schema='public' and table_name=%s order by ordinal_position""", (t,))]


def missing_rows(t, where=None):
    k = pk_cols(local, t)
    cl, cp = cols(local, t), cols(prod, t)
    shared = [c for c in cl if c in cp]
    pkeys = set(tuple(r) for r in q(prod, 'select %s from public."%s"'
                                    % (",".join('"%s"' % c for c in k), t)))
    sql = 'select %s from public."%s"' % (",".join('"%s"' % c for c in shared), t)
    if where:
        sql += " where " + where
    rows = q(local, sql)
    idx = [shared.index(c) for c in k]
    return shared, [r for r in rows if tuple(r[i] for i in idx) not in pkeys]


# ---------- A. 以模型為權威對齊欄位寬度 ----------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "betweencoffee_delivery.settings")
django.setup()
from django.db.models import CharField, EmailField  # noqa: E402
from eshop.models import OrderModel  # noqa: E402

model_limits = {}
for f in OrderModel._meta.get_fields():
    if isinstance(f, (CharField, EmailField)) and f.max_length:
        model_limits[f.column] = f.max_length

prod_widths = {r[0]: r[1] for r in q(prod, """select column_name, character_maximum_length
    from information_schema.columns where table_schema='public' and table_name='eshop_ordermodel'
    and data_type like 'character%'""")}
max_len = {c: q(local, 'select coalesce(max(length("%s"::text)),0) from public."eshop_ordermodel"' % c)[0][0]
           for c in model_limits}
prod_max_len = {c: q(prod, 'select coalesce(max(length("%s"::text)),0) from public."eshop_ordermodel"' % c)[0][0]
                for c in model_limits}

print("=== A. 以模型對齊正式庫 varchar 寬度 ===")
alters = []
for c, want in sorted(model_limits.items()):
    have = prod_widths.get(c)
    if have is None or have == want:
        continue
    if have < want or prod_max_len.get(c, 0) <= want:
        alters.append((c, have, want))
        print("   %-24s 正式 %-5s → 模型 %-5s（正式現有最長 %s / 本地最長 %s 字元）"
              % (c, have, want, prod_max_len.get(c), max_len.get(c)))
    else:
        print("   %-24s 跳過：正式 %s > 模型 %s，但正式已有 %s 字元的值 ✗"
              % (c, have, want, prod_max_len.get(c)))
if not alters:
    print("   （無需調整）")

print("\n=== B~D. 待寫入計畫 ===")
shared_u, users = missing_rows("auth_user")
uid_i = shared_u.index("id")
users = [r for r in users if r[uid_i] not in USER_REMAP]
for flag, val in FORCE_FLAGS.items():
    if flag in shared_u:
        j = shared_u.index(flag)
        users = [tuple(val if i == j else v for i, v in enumerate(r)) for r in users]
print("   auth_user（降權+停用）           %4d 筆" % len(users))

shared_o, orders = missing_rows("eshop_ordermodel")
id_i = shared_o.index("id")
if "user_id" in shared_o:
    j = shared_o.index("user_id")
    orders = [tuple(USER_REMAP.get(v, v) if i == j else v for i, v in enumerate(r)) for r in orders]

remap_log = {}
uniq_o = set(uq_cols(prod, "eshop_ordermodel"))
for col in sorted(set(uniq_o) | set(model_limits)):
    if col not in shared_o or col not in model_limits:
        continue
    ci, limit = shared_o.index(col), model_limits[col]
    used = set(r[0] for r in q(prod, 'select "%s" from public."eshop_ordermodel"' % col) if r[0] is not None)
    n, changed, out = 9000, [], []
    for r in orders:
        v = r[ci]
        s = None if v is None else str(v)
        over = s is not None and len(s) > limit
        clash = s is not None and col in uniq_o and v in used
        if s is None:
            out.append(r)
            continue
        if not over and not clash:
            used.add(v)
            out.append(r)
            continue
        if col in uniq_o:
            m = re.match(r"^(.*-)?(\d{2,})$", s)
            pre = (m.group(1) or "") if m else ""
            if m and len(pre) + 4 <= limit:
                nxt = 9000
                while (pre + str(nxt)) in used or len(pre + str(nxt)) > limit:
                    nxt += 1
                nv = pre + str(nxt)
            else:
                ts = str(r[shared_o.index("created_at")] or "")[:10].replace("-", "") or "00000000"
                while True:
                    nv = ("BC-%s-%04d" % (ts, n))[:limit]
                    n += 1
                    if nv not in used:
                        break
        else:
            nv = s[:limit]
        used.add(nv)
        changed.append((r[id_i], s, nv))
        out.append(tuple(nv if k == ci else x for k, x in enumerate(r)))
    orders = out
    if changed:
        remap_log[col] = changed
        print("   %s 改派/截斷 %d 筆，例 %s" % (col, len(changed), changed[:3]))
print("   eshop_ordermodel                %4d 筆" % len(orders))

new_order_ids = [r[id_i] for r in orders]
o_list = "(%s)" % (",".join(str(i) for i in new_order_ids) or "null")
s_q, queue_rows = missing_rows("eshop_coffeequeue", "order_id in " + o_list)
for col in uq_cols(prod, "eshop_coffeequeue"):
    if col not in s_q:
        continue
    ci = s_q.index(col)
    used = set(r[0] for r in q(prod, 'select "%s" from public."eshop_coffeequeue"' % col) if r[0] is not None)
    kept = [r for r in queue_rows if r[ci] is None or r[ci] not in used]
    for r in kept:
        used.add(r[ci])
    if len(kept) != len(queue_rows):
        print("   （佇列 %s 略過 %d 筆撞號）" % (col, len(queue_rows) - len(kept)))
        queue_rows = kept
print("   eshop_coffeequeue               %4d 筆" % len(queue_rows))

if not APPLY:
    print("\n（乾跑結束；加 --apply 才寫入）")
    prod.close()
    local.close()
    sys.exit(0)

try:
    with prod:
        cur = prod.cursor()
        for c, have, want in alters:
            cur.execute('alter table public."eshop_ordermodel" alter column "%s" type varchar(%d)' % (c, want))
            print("   ✔ ALTER %s %s → %s" % (c, have, want))
        for t, sh, rows in (("auth_user", shared_u, users),
                            ("eshop_ordermodel", shared_o, orders),
                            ("eshop_coffeequeue", s_q, queue_rows)):
            if not rows:
                continue
            types = {r[0]: r[1] for r in q(prod, """select column_name, data_type from information_schema.columns
                     where table_schema='public' and table_name=%s""", (t,))}
            jidx = [i for i, c in enumerate(sh) if types.get(c) in ("json", "jsonb")]
            data = [tuple(Json(v) if i in jidx else v for i, v in enumerate(r)) for r in rows] if jidx else rows
            execute_values(cur, 'insert into public."%s" (%s) values %%s'
                           % (t, ",".join('"%s"' % c for c in sh)), data, page_size=200)
            print("   ✔ %-24s 寫入 %d 筆" % (t, len(rows)))
        print("   --- sequence 修正 ---")
        for t in ("auth_user", "eshop_ordermodel", "eshop_coffeequeue"):
            cur.execute("SAVEPOINT s1")
            try:
                cur.execute("""select setval(pg_get_serial_sequence('public."%s"','id'),
                               coalesce((select max(id) from public."%s"),1))""" % (t, t))
                cur.execute('select max(id) from public."%s"' % t)
                print("      %-24s max(id)=%s" % (t, cur.fetchone()[0]))
                cur.execute("RELEASE SAVEPOINT s1")
            except Exception as e:
                cur.execute("ROLLBACK TO SAVEPOINT s1")
                print("      %-24s 略過：%s" % (t, str(e)[:45]))
    print("\n✔ 已 commit")
except Exception as e:
    print("\n✘ 失敗 → rollback（正式庫未變更）:", str(e)[:250])

print("\n=== 寫入後筆數 ===")
for t in ("auth_user", "eshop_ordermodel", "eshop_coffeequeue"):
    a = q(prod, 'select count(*) from public."%s"' % t)[0][0]
    b = q(local, 'select count(*) from public."%s"' % t)[0][0]
    print("   %-24s 正式 %5d / 本地 %5d %s" % (t, a, b, "✓" if a == b else "← 仍不同"))
prod.close()
local.close()
