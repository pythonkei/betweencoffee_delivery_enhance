#!/usr/bin/env python3
"""統一正式庫資料（2026-09-15）

背景：回補時以 PK(id) 去重比對，但本地 id=62（test_customer）與正式 id=62（fb_kei）
是不同人 → test_customer 漏建、其 5 筆訂單被錯掛到 fb_kei；另有 31 筆舊訂單在正式庫
為無主（本地為 fb_kei）。本腳本以 **username 為橋樑** 重新對齊：

  A. 補建缺漏帳號（比照先前：降權 is_superuser/is_staff=False + 停用 is_active=False）
  B. 逐筆訂單重新對齊歸屬：本地 user → username → 正式 user id
  C. 覆蓋正式庫咖啡名稱（以本地為準，差異者才更新）
  D. 修正 sequence
單一 transaction，任何錯誤 rollback。用法：python3 scripts/unify_prod_data_20260915.py [--apply]
"""

import re
import sys

import psycopg2

APPLY = "--apply" in sys.argv
ENV = "/home/kei/Desktop/betweencoffee_delivery_enhance/.env"

line = next(l for l in open(ENV, encoding="utf-8").read().split("\n") if "DATABASE_URL=" in l and "pooler" in l)
pu_, pp_, ph, pport, _ = re.search(r"DATABASE_URL=postgresql://([^:]+):([^@]+)@([^:/]+):(\d+)/(\S*)", line).groups()
prod = psycopg2.connect(host=ph, port=int(pport), user=pu_, password=pp_, dbname="postgres",
                        sslmode="require", connect_timeout=20)
local = psycopg2.connect(host="127.0.0.1", port=5432, user="postgres", password="postgres",
                         dbname="betweencoffee_delivery_db", connect_timeout=10)


def q(c, sql, a=None):
    cur = c.cursor()
    cur.execute(sql, a)
    return cur.fetchall()


def cols(c, t):
    return [r[0] for r in q(c, """select column_name from information_schema.columns
        where table_schema='public' and table_name=%s order by ordinal_position""", (t,))]


lu = {r[0]: r[1] for r in q(local, "select id, username from auth_user")}
pname = {r[1]: r[0] for r in q(prod, "select id, username from auth_user")}

# ---------- A. 補建缺漏帳號（計畫）----------
shared_u = [c for c in cols(local, "auth_user") if c in cols(prod, "auth_user")]
new_users = []
for i in sorted(lu):
    if lu[i] in pname:
        continue
    cur = local.cursor()
    cur.execute('select %s from public."auth_user" where id=%%s' % ",".join('"%s"' % c for c in shared_u), (i,))
    r = dict(zip(shared_u, cur.fetchone()))
    r.pop("id", None)
    for f in ("is_superuser", "is_staff", "is_active"):
        if f in r:
            r[f] = False
    new_users.append(r)
print("=== A. 補建缺漏帳號（降權 + 停用）===")
for r in new_users:
    n = q(local, "select count(*) from eshop_ordermodel where user_id=%s",
          ({v: k for k, v in lu.items()}[r["username"]],))[0][0]
    print("   + %-22s email=%-24s 訂單 %s 筆" % (r["username"], r.get("email") or "-", n))
if not new_users:
    print("   （無）")

# ---------- B. 訂單歸屬重新對齊（計畫，以 username 表達）----------
print("\n=== B. 訂單歸屬重新對齊（本地 user → username → 正式 user id）===")
tgt_name = {}
lost = set()
for oid, uid in q(local, "select id, user_id from eshop_ordermodel order by id"):
    if uid is None:
        tgt_name[oid] = None
    else:
        name = lu.get(uid)
        tgt_name[oid] = name
        if name not in pname and name not in [r["username"] for r in new_users]:
            lost.add(name)
if lost:
    print("   ✗ 找不到對應帳號（將設為無主）:", sorted(str(x) for x in lost))
cur_prod = dict(q(prod, "select id, user_id from eshop_ordermodel"))
p_user = {r[0]: r[1] for r in q(prod, "select id, username from auth_user")}
plan_upd = []
for oid, name in tgt_name.items():
    if oid not in cur_prod:
        continue
    want = None if name is None else pname.get(name)
    have = cur_prod[oid]
    same = (want == have) or (want is None and have is None) or \
           (name is not None and have is not None and p_user.get(have) == name)
    if not same:
        plan_upd.append((oid, have, name))
print("   需更新 %d 筆（共比對 %d 筆；其中新帳號 %d 個）" % (len(plan_upd), len(tgt_name), len(new_users)))
for oid, have, name in plan_upd[:10]:
    print("      order id=%-6s 正式 %-6s → %s" % (oid, have, name))
if len(plan_upd) > 10:
    print("      …其餘 %d 筆" % (len(plan_upd) - 10))

# ---------- C. 咖啡名稱覆蓋（計畫）----------
print("\n=== C. 咖啡名稱覆蓋（以本地為準）===")
pn = {r[0]: r[1] for r in q(prod, "select id, name from eshop_coffeeitem")}
ln = {r[0]: r[1] for r in q(local, "select id, name from eshop_coffeeitem")}
name_changes = [(i, pn[i], ln[i]) for i in sorted(set(pn) & set(ln)) if pn[i] != ln[i]]
for i, a, b in name_changes:
    print("   id=%-3s %s → %s" % (i, a, b))
if not name_changes:
    print("   （無差異）")

# ---------- 執行 ----------
if not APPLY:
    print("\n（乾跑結束；加 --apply 才寫入）")
    prod.close()
    local.close()
    sys.exit(0)

try:
    with prod:
        from psycopg2.extras import execute_values
        cur = prod.cursor()
        # A. 補建帳號
        for r in new_users:
            cs = [c for c in shared_u if c in r and c != "id"]
            cur.execute('insert into public."auth_user" (%s) values (%s)'
                        % (",".join('"%s"' % c for c in cs), ",".join(["%s"] * len(cs))),
                        [r[c] for c in cs])
            print("   ✔ 建立帳號 %-22s（降權+停用）" % r["username"])
        pnow = {r[1]: r[0] for r in q(prod, "select id, username from auth_user")}
        # B. 訂單歸屬
        upd = []
        for oid, have, name in plan_upd:
            if name is None:
                upd.append((oid, None))
                continue
            want = pnow.get(name)
            if want is None:
                print("   ✗ 帳號 %s 不存在，略過 order %s" % (name, oid))
                continue
            upd.append((oid, want))
        if upd:
            execute_values(cur, 'update public."eshop_ordermodel" o set user_id=d.uid '
                                'from (values %s) d(id, uid) where o.id=d.id',
                           upd, template="(%s::int, %s::int)", page_size=500)
        print("   ✔ 訂單歸屬更新 %d 筆" % len(upd))
        # C. 咖啡名稱
        for i, a, b in name_changes:
            cur.execute("update public.eshop_coffeeitem set name=%s where id=%s", (b, i))
        print("   ✔ 咖啡名稱更新 %d 款" % len(name_changes))
        # D. sequence
        for t in ("auth_user", "eshop_ordermodel"):
            cur.execute("SAVEPOINT s1")
            try:
                cur.execute("""select setval(pg_get_serial_sequence('public."%s"','id'),
                               coalesce((select max(id) from public."%s"),1))""" % (t, t))
                cur.execute("RELEASE SAVEPOINT s1")
                print("      %s sequence 已修正" % t)
            except Exception as e:
                cur.execute("ROLLBACK TO SAVEPOINT s1")
                print("      %s sequence 略過：%s" % (t, str(e)[:40]))
    print("\n✔ 已 commit")
except Exception as e:
    print("\n✘ 失敗 → rollback（正式庫未變更）:", str(e)[:250])

print("\n=== 驗證：訂單歸屬（依 username，含舊+新全部訂單）===")
def byname(c):
    return dict(q(c, """select coalesce(u.username,'(無主)'), count(*) from eshop_ordermodel o
                        left join auth_user u on u.id=o.user_id group by 1 order by 1"""))
a, b = byname(prod), byname(local)
bad = 0
for k in sorted(set(a) | set(b)):
    x, y = a.get(k, 0), b.get(k, 0)
    if x != y:
        bad += 1
        print("   %-26s 正式=%-5s 本地=%-5s ✗" % (k, x, y))
print("   ✓ 完全一致（%d 個帳號）" % len(set(a) | set(b)) if not bad else "   ✗ %d 個不一致" % bad)
print("\n=== 驗證：咖啡名稱 ===")
pn2 = {r[0]: r[1] for r in q(prod, "select id, name from eshop_coffeeitem")}
d = [(i, pn2[i], ln[i]) for i in sorted(set(pn2) & set(ln)) if pn2[i] != ln[i]]
print("   差異 %d 款 %s" % (len(d), "" if not d else str(d)))
print("\n=== 筆數 / 帳號數 ===")
for t in ("auth_user", "eshop_ordermodel", "eshop_coffeequeue"):
    x = q(prod, 'select count(*) from public."%s"' % t)[0][0]
    y = q(local, 'select count(*) from public."%s"' % t)[0][0]
    print("   %-22s 正式 %5d / 本地 %5d %s" % (t, x, y, "✓" if x == y else "← 不同"))
prod.close()
local.close()
