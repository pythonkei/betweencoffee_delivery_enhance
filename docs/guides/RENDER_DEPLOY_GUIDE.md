# Between Coffee — Render 免費部署指南

> **適用版本**: v2.0+
> **部署平台**: Render (永久免費)
> **用途**: 面試展示 / 個人作品集
> **最後更新**: 2026-06-08

---

## 📋 目錄

1. [方案概述](#1-方案概述)
2. [前置準備](#2-前置準備)
3. [一鍵部署（最快）](#3-一鍵部署最快)
4. [手動部署（逐步）](#4-手動部署逐步)
5. [環境變數設定](#5-環境變數設定)
6. [資料庫遷移](#6-資料庫遷移)
7. [驗證部署](#7-驗證部署)
8. [常見問題](#8-常見問題)

---

## 1. 方案概述

### 使用服務

| 服務 | 方案 | 費用 | 說明 |
|:----|:----|:----|:-----|
| **Web Service** | Free | **$0 永久** | 750 小時/月，15 分鐘無活動休眠 |
| **PostgreSQL** | Free | **$0 永久** | 1GB 儲存 |
| **Cron Job** | Free | **$0 永久** | 替代 Celery Beat，每 5 分鐘檢查未支付訂單 |

### 功能支援對照

| 功能 | Railway (舊) | Render (新) | 說明 |
|:----|:-----------:|:----------:|:----|
| Django Web | ✅ | ✅ | gunicorn WSGI |
| PostgreSQL | ✅ | ✅ | Render 內建 |
| 靜態文件 | ✅ | ✅ | WhiteNoise |
| 自訂域名 | ✅ | ✅ | Render Dashboard 設定 |
| HTTPS | ✅ | ✅ | 自動 |
| 休眠 | ❌ 不休眠 | ⚠️ 15分鐘 | 展示用可接受 |
| Redis | ✅ | ❌ 無 | 展示用不需要 |
| Celery | ✅ | ❌ 無 | 用 Cron Job 替代 |
| WebSocket | ✅ | ❌ 無 | 頁面仍可正常瀏覽 |

---

## 2. 前置準備

### 2.1 必要帳號

- [ ] **GitHub 帳號** — 存放程式碼
- [ ] **Render 帳號** — 註冊 https://dashboard.render.com （使用 GitHub 登入，不需信用卡）

### 2.2 本地環境檢查

```bash
# 確認專案目錄結構
cd /home/kei/Desktop/betweencoffee_delivery_enhance
ls -la

# 確認 render.yaml 存在（一鍵部署配置）
cat render.yaml

# 確認 requirements.txt 存在
cat requirements.txt | head -20
```

### 2.3 確認必要檔案存在

部署前請確認以下檔案都已存在於專案根目錄：

```
betweencoffee_delivery_enhance/
├── render.yaml              # ✅ Render 一鍵部署配置（已建立）
├── requirements.txt         # ✅ Python 依賴
├── Procfile                 # ✅ 程序啟動配置
├── manage.py                # ✅ Django 管理腳本
├── betweencoffee_delivery/
│   ├── settings.py          # ✅ 已加入 Render 相容性
│   ├── wsgi.py              # ✅ WSGI 應用
│   └── asgi.py              # ✅ ASGI 應用
└── static/
    └── ...                  # ✅ 靜態文件
```

---

## 3. 一鍵部署（最快）

### 步驟 1：推送程式碼到 GitHub

```bash
# 確保所有變更都已提交
git add .
git commit -m "feat: add Render deployment support"

# 推送到 GitHub
git push origin main
```

### 步驟 2：使用 Blueprint 部署（建立 Web Service）

1. 登入 Render Dashboard → https://dashboard.render.com
2. 點擊 **New +** → **Blueprint**
3. 選擇你的 GitHub 倉庫：`pythonkei/betweencoffee_delivery_enhance`
4. Render 會自動讀取 `render.yaml` 並建立 **Web Service**
5. 點擊 **Apply** 開始部署

> ⚠️ **注意**：Blueprint 僅支援 `web` 服務類型。PostgreSQL 和 Cron Job 需手動建立（見下方步驟）。

### 步驟 3：等待 Web Service 部署完成

- 首次部署約需 **3-5 分鐘**
- 可在 Dashboard 查看即時日誌
- 部署完成後會顯示 `https://betweencoffee.onrender.com`
- **此時網站還無法正常運行**，因為還沒有資料庫

### 步驟 4：手動建立 PostgreSQL 資料庫

1. Render Dashboard → **New +** → **PostgreSQL**
2. 設定：

| 設定項 | 值 |
|:------|:---|
| **Name** | `betweencoffee-db` |
| **Database** | `betweencoffee_delivery_db` |
| **User** | 自動生成 |
| **Region** | `Singapore` |
| **Plan** | **Free** |

3. 建立後，複製 **Internal Database URL**

### 步驟 5：連接資料庫到 Web Service

1. 進入 Web Service Dashboard → **Environment** 頁籤
2. 新增環境變數：
   - `DATABASE_URL` → 貼上 Internal Database URL
   - `IS_RENDER` → `True`
   - `SECRET_KEY` → 點擊 **Generate** 自動生成
   - `DEBUG` → `False`
3. 點擊 **Save Changes** → 服務會自動重新部署

### 步驟 6：手動建立 Cron Job（替代 Celery Beat）

1. Render Dashboard → **New +** → **Cron Job**
2. 設定：

| 設定項 | 值 |
|:------|:---|
| **Name** | `monitor-pending-payments` |
| **Region** | `Singapore` |
| **Branch** | `main` |
| **Schedule** | `*/5 * * * *`（每 5 分鐘） |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python manage.py cancel_expired_pending_orders` |
| **Plan** | **Free** |

3. 環境變數（與 Web Service 相同）：
   - `DATABASE_URL` → 同一個 Internal Database URL
   - `IS_RENDER` → `True`
   - `SECRET_KEY` → 同一個 SECRET_KEY
   - `DEBUG` → `False`
   - `DJANGO_SETTINGS_MODULE` → `betweencoffee_delivery.settings`
   - `PYTHON_VERSION` → `3.11.0`

---

## 4. 手動部署（逐步）

如果一鍵部署有問題，可以手動建立每個服務。

### 4.1 建立 Web Service

1. Render Dashboard → **New +** → **Web Service**
2. 連接你的 GitHub 倉庫
3. 設定：

| 設定項 | 值 |
|:------|:---|
| **Name** | `betweencoffee` |
| **Region** | `Singapore`（亞洲最快） |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install --upgrade pip && pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| **Start Command** | `python manage.py migrate --noinput || echo "Migration failed, continuing anyway..." && gunicorn betweencoffee_delivery.wsgi:application --bind 0.0.0.0:$PORT --workers=2 --timeout=120` |
| **Health Check Path** | `/health/` |
| **Plan** | **Free** |

### 4.2 建立 PostgreSQL 資料庫

1. Render Dashboard → **New +** → **PostgreSQL**
2. 設定：

| 設定項 | 值 |
|:------|:---|
| **Name** | `betweencoffee-db` |
| **Database** | `betweencoffee_delivery_db` |
| **User** | 自動生成 |
| **Region** | `Singapore` |
| **Plan** | **Free** |

3. 建立後，複製 **Internal Database URL**（格式：`postgres://user:password@host:port/dbname`）

### 4.3 連接資料庫到 Web Service

1. 進入 Web Service Dashboard → **Environment** 頁籤
2. 新增環境變數：
   - `DATABASE_URL` → 貼上 Internal Database URL
   - `IS_RENDER` → `True`
   - `SECRET_KEY` → 點擊 **Generate** 自動生成
   - `DEBUG` → `False`
3. 點擊 **Save Changes** → 服務會自動重新部署

### 4.4 建立 Cron Job（替代 Celery Beat）

1. Render Dashboard → **New +** → **Cron Job**
2. 設定：

| 設定項 | 值 |
|:------|:---|
| **Name** | `monitor-pending-payments` |
| **Region** | `Singapore` |
| **Branch** | `main` |
| **Schedule** | `*/5 * * * *`（每 5 分鐘） |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python manage.py cancel_expired_pending_orders` |
| **Plan** | **Free** |

3. 環境變數（與 Web Service 相同）：
   - `DATABASE_URL` → 同一個 Internal Database URL
   - `IS_RENDER` → `True`
   - `SECRET_KEY` → 同一個 SECRET_KEY
   - `DEBUG` → `False`

---

## 5. 環境變數設定

### 必要環境變數

| 變數名稱 | 說明 | 範例值 |
|:---------|:-----|:-------|
| `DATABASE_URL` | PostgreSQL 連線字串 | Render 自動提供 |
| `SECRET_KEY` | Django 密鑰 | Render 自動生成 |
| `IS_RENDER` | Render 環境標記 | `True` |
| `DEBUG` | 除錯模式 | `False` |

### 可選環境變數（展示用可留空）

| 變數名稱 | 說明 | 備註 |
|:---------|:-----|:-----|
| `EMAIL_HOST_USER` | Gmail 帳號 | 用於發送郵件 |
| `EMAIL_HOST_PASSWORD` | Gmail 應用密碼 | 用於發送郵件 |
| `PAYPAL_CLIENT_ID` | PayPal Client ID | 展示用可留空 |
| `PAYPAL_CLIENT_SECRET` | PayPal Secret | 展示用可留空 |
| `ALIPAY_APP_ID` | 支付寶 App ID | 展示用可留空 |
| `OAUTH_GOOGLE_CLIENT_ID` | Google OAuth ID | 展示用可留空 |
| `OAUTH_GOOGLE_SECRET` | Google OAuth Secret | 展示用可留空 |
| `OAUTH_FACEBOOK_CLIENT_ID` | Facebook OAuth ID | 展示用可留空 |
| `OAUTH_FACEBOOK_SECRET` | Facebook OAuth Secret | 展示用可留空 |

---

## 6. 資料庫遷移

### 方法一：從本地 PostgreSQL 匯出資料

```bash
# 1. 本地備份資料庫
pg_dump -U postgres -h localhost betweencoffee_delivery_db > coffee_backup.sql

# 2. 連接到 Render PostgreSQL（使用 psql）
psql "$DATABASE_URL" < coffee_backup.sql
```

### 方法二：使用 Django 管理命令

```bash
# 1. 在本地建立資料快照
python manage.py dumpdata --natural-foreign --natural-primary -o data_dump.json

# 2. 上傳到 Render
# 使用 Render Shell 功能上傳檔案
```

### 方法三：使用 pgAdmin（圖形化）

1. 在 Render PostgreSQL Dashboard 取得 **External Connection** 資訊
2. 在 pgAdmin 中建立新的 Server 連線
3. 使用 **Restore** 功能還原備份檔案

---

## 7. 驗證部署

### 7.1 基本檢查

部署完成後，訪問你的 Render URL：

```
https://betweencoffee.onrender.com
```

檢查以下功能是否正常：

- [ ] 首頁正常載入
- [ ] CSS/JS 靜態文件正確顯示
- [ ] 咖啡菜單頁面可瀏覽
- [ ] 購物車功能正常
- [ ] 會員登入/註冊
- [ ] 管理後台可訪問

### 7.2 檢查部署日誌

```bash
# 在 Render Dashboard → Web Service → Logs
# 查看啟動日誌，確認沒有錯誤
```

### 7.3 檢查 Cron Job

```bash
# 在 Render Dashboard → Cron Job → Logs
# 確認每 5 分鐘有執行記錄
```

---

## 8. 常見問題

### Q1: 網站載入很慢？

**原因**：Render Free 方案在 15 分鐘無活動後會休眠。
**解決**：首次訪問需等待 5-10 秒喚醒，之後正常速度。

### Q2: 靜態文件（CSS/JS）無法載入？

**原因**：`collectstatic` 未正確執行。
**解決**：在 Render Dashboard 手動執行：
```bash
python manage.py collectstatic --noinput
```

### Q3: 資料庫連線失敗？

**原因**：`DATABASE_URL` 環境變數未正確設定。
**解決**：檢查 Web Service → Environment → DATABASE_URL 是否正確。

### Q4: 如何綁定自訂域名？

1. Render Dashboard → Web Service → **Settings**
2. 在 **Custom Domain** 區塊輸入你的域名
3. 在 DNS 管理後台新增 CNAME 記錄指向 `onrender.com`
4. Render 會自動申請 SSL 憑證

### Q5: 如何避免休眠？

Free 方案無法避免休眠。如果需要 24/7 運行，可升級到 **Starter** 方案（$7/月）。

### Q6: 資料庫 90 天後會怎樣？

Render Free PostgreSQL 90 天後會要求升級。解決方案：
1. 升級到 **Starter** 方案（$7/月）
2. 或到期前匯出資料，刪除後重新建立新的 Free 資料庫

---

## 📝 備忘錄

### Render Dashboard 連結

- Web Service: https://dashboard.render.com/web/srv-xxxxx
- PostgreSQL: https://dashboard.render.com/db/dpg-xxxxx
- Cron Job: https://dashboard.render.com/cron/cron-xxxxx

### 常用指令

```bash
# 查看部署日誌
# Render Dashboard → Web Service → Logs

# 手動觸發 Cron Job
# Render Dashboard → Cron Job → Manual Run

# 連接到資料庫
psql "$DATABASE_URL"

# 執行 Django 管理命令
# Render Dashboard → Web Service → Shell
python manage.py check
python manage.py showmigrations
```

---

> **提示**：部署完成後，建議在面試時展示以下功能：
> 1. 咖啡菜單瀏覽與購物車流程
> 2. 會員登入與訂單歷史
> 3. 管理後台訂單管理
> 4. 響應式設計（手機/平板/桌面）
