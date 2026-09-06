# 開發標準與規範

> 引用自: BETWEEN_COFFEE_SYSTEM_REPORT.md 第7章

## 開發環境

### 本地開發

```bash
# 1. 克隆專案
git clone https://github.com/pythonkei/betweencoffee_delivery_enhance.git
cd betweencoffee_delivery_enhance

# 2. 創建虛擬環境
python -m venv venv
source venv/bin/activate

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 環境變量
cp .env.example .env
# 編輯 .env 設置必要變量

# 5. 數據庫遷移
python manage.py migrate

# 6. 創建超級用戶
python manage.py createsuperuser

# 7. 運行開發服務器
python manage.py runserver
```

### 生產環境（Render）

| 配置項 | 值 |
|--------|-----|
| 部署方式 | Docker (Dockerfile) |
| 啟動命令 | `python manage.py migrate && daphne -b 0.0.0.0 -p \$PORT betweencoffee_delivery.asgi:application` |
| Auto Deploy | 啟用 |
| 數據庫 | Render Postgres |
| Redis | 無（使用 InMemoryChannelLayer + MockCelery） |

## 開發規範

### 程式碼風格

| 語言 | 工具 | 配置 |
|------|------|------|
| Python | flake8, black, isort | `pyproject.toml` |
| JavaScript | ESLint | 待配置 |
| CSS | Stylelint | 待配置 |

### 提交規範

```
feat: 新增功能
fix: 修復問題
docs: 文檔更新
style: 代碼格式調整
refactor: 代碼重構
test: 測試相關
chore: 構建/工具變動
```

### 分支策略

```
main        → 生產環境
develop     → 開發環境
feature/*   → 功能開發
bugfix/*    → 問題修復
hotfix/*    → 緊急修復
```

## 常見開發任務速查

### 新增 API 端點

```python
# 1. 在 eshop/views/api_views.py 新增視圖
# 2. 在 eshop/urls_api.py 註冊路由
# 3. 在前端 JS 中調用
```

### 新增 WebSocket 事件

```python
# 後端: 在 eshop/consumers.py 新增事件處理
async def handle_new_event(self, event):
    await self.send_json({
        'type': 'new_event',
        'data': event['data']
    })

# 前端: 在 websocket-core.js 監聽事件
WebSocketCore.getInstance().on('message:new_event', (data) => {
    // 處理邏輯
});
```

### 新增數據庫遷移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 新增頁面模板

```python
# 1. 創建模板文件 templates/xxx.html
# 2. 在 eshop/views/xxx_views.py 新增視圖
# 3. 在 eshop/urls_xxx.py 註冊路由
# 4. 在 eshop/urls.py 引入子路由
```

## 除錯指南

### WebSocket 連接問題

```bash
# 1. 檢查 ASGI 配置
#    betweencoffee_delivery/asgi.py

# 2. 檢查 Channels 配置
#    betweencoffee_delivery/settings.py → CHANNEL_LAYERS

# 3. 檢查消費者
#    eshop/consumers.py

# 4. 檢查前端連接
#    static/js/websocket-core.js

# 5. 檢查 WebSocket 路由
#    eshop/routing.py
```

### 支付問題

```bash
# 1. 檢查環境變量
#    PAYPAL_CLIENT_ID, ALIPAY_APP_ID 等

# 2. 檢查支付視圖
#    eshop/views/payment_views.py

# 3. 檢查支付工具
#    eshop/paypal_utils.py, eshop/alipay_utils.py

# 4. 檢查訂單狀態管理
#    eshop/order_status_manager.py
```

### 數據庫問題

```bash
# 1. 檢查遷移狀態
python manage.py showmigrations

# 2. 檢查模型
#    eshop/models.py

# 3. 檢查查詢
#    使用 Django Debug Toolbar 分析
```
