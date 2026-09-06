# Between Coffee 系統 - 技術架構（精簡版）

> **注意**: 此文件僅包含 `.clinerules` 中未涵蓋的獨特技術資訊。
> 通用架構概覽請參閱 `.clinerules/.clinerules`。
>
> **⚠️ 資料庫結構過時警告**: 此文件中的 SQL DDL 與索引定義為早期版本（migration 0001 ~ 0010），
> 經過從 **0045 到 0053** 共 9 次結構性遷移（包含字段增減、關聯調整、預設值修正等）後，
> 當前資料庫結構與此處描述的 DDL 已有顯著差異。請以 `eshop/models/` 目錄下的模型定義為準。
>
> | 遷移範圍 | 說明 |
> |:---------|:------|
> | 0045 | 同步遺留資料庫字段 |
> | 0046 | CoffeeQueue 新增 is_expedited |
> | 0047 | 修復 Barista 表結構 |
> | 0048 | 新增 order_number 欄位 |
> | 0049 | 新增 discount 欄位 |
> | 0050 | 補充 0045 遺漏欄位 |
> | 0051 | 合併 0047 與 0050 |
> | 0052 | 移除 pickup_time 改為 pickup_time_choice |
> | 0053 | CoffeeQueue 預設值修正 |

## 🗄️ 資料庫設計

### 主要表結構

#### OrderModel 表
```sql
CREATE TABLE eshop_ordermodel (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE,
    customer_name VARCHAR(100),
    customer_email VARCHAR(254),
    total_amount DECIMAL(10, 2),
    payment_status VARCHAR(20),
    payment_method VARCHAR(20),
    status VARCHAR(20),
    pickup_code VARCHAR(10),
    qr_code_data TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    preparation_started_at TIMESTAMP WITH TIME ZONE,
    ready_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);
```

#### 索引設計
```sql
-- 訂單查詢優化
CREATE INDEX idx_order_status ON eshop_ordermodel(status);
CREATE INDEX idx_order_created ON eshop_ordermodel(created_at);
CREATE INDEX idx_order_payment ON eshop_ordermodel(payment_status);

-- 隊列查詢優化
CREATE INDEX idx_queue_status ON eshop_coffeequeue(status);
CREATE INDEX idx_queue_barista ON eshop_coffeequeue(barista_id);
```

## 🔐 安全架構

### 權限層級
1. **顧客權限**: 查看菜單、下單、查看自己的訂單
2. **員工權限**: 查看隊列、更新訂單狀態、管理製作
3. **管理員權限**: 所有系統功能、數據管理、用戶管理

### 數據保護
- **支付信息**: 不存儲原始卡號，使用支付網關令牌
- **用戶密碼**: bcrypt 哈希存儲
- **API 密鑰**: 環境變量管理，不寫入代碼
- **HTTPS**: 生產環境強制 HTTPS + HSTS 頭
- **CSRF**: Django 內建 CSRF 保護

## 💎 忠誠度計畫技術實現

### 系統架構
- **核心模型**: `CustomerLoyalty`, `CustomerCoupon`, `CustomerActivity`
- **積分系統**: 消費獲取積分，積分兌換優惠券
- **優惠券系統**: 百分比折扣、固定金額、免費商品
- **會員等級**: 簡化設計，已移除傳統的 Bronze/Silver/Gold 等級

### 價格計算邏輯（當前版本）
```python
def _calculate_price(self, product, product_type, weight=None):
    """計算商品價格 - 當前版本沒有會員折扣"""
    if product_type == 'bean' and weight:
        return product.get_price(weight)
    elif product_type == 'coffee':
        return product.price
    return 0
```

### 積分獲取規則
- **消費積分**: 每消費 $10 = 1 積分
- **活動積分**: 參與活動獲得額外積分

### 優惠券類型
1. **百分比折扣**: 如 5% 折扣
2. **固定金額**: 如 $5 折扣
3. **免費商品**: 指定商品免費
4. **最低消費限制**: 優惠券使用條件

### 關鍵發現（2026-04-10 分析）
- ❌ **沒有自動會員折扣機制**: 系統不提供基於會員等級的自動折扣
- ✅ **優惠券折扣**: 所有折扣通過優惠券系統實現
- ✅ **價格顯示**: 所有客戶看到相同價格，沒有會員價顯示
- ✅ **積分系統**: 功能完整，支持積分獲取和兌換

### 相關文件
- `socialuser/models_enhanced.py`: 會員模型定義
- `cart/cart.py`: 價格計算邏輯
- `eshop/models.py`: 產品價格設定
- `socialuser/views_enhanced.py`: 會員相關視圖
- `socialuser/templates/socialuser/loyalty_dashboard.html`: 忠誠度儀表板

---
**最後更新**: 2026-07-25（從 508 行精簡為當前版本）  
**注意**: 原始版本包含已過時的 Railway/Redis/jQuery 參考，已移除。通用技術架構請參閱 `.clinerules/.clinerules`。