# Between Coffee CSS 引用審計報告

> **執行時間**: 自動產生 ｜ **模板數**: 8 ｜ **CSS 檔案數**: 20

## 摘要

- **被引用 CSS**: 20 個（約 1450 KB）
- **死資產（未被引用）**: 0 個（約 0 KB）
- **僅特定頁面載入**: 8 個
- **重複引用（多模板）**: 13 個
- **全部 CSS 總量**: 約 1450 KB

## 被引用 CSS（base.html 全域 + 特定頁面）

| CSS 檔案 | 大小 | 引用模板 |
|---|---:|---|
| animate-custom.css (🟢 全域) | 6KB | templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html |
| bc-attract.css (🟢 全域) | 7KB | templates/betweencoffee_delivery/base.html |
| bc-components.css (🟢 全域) | 90KB | templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html |
| bc-search.css (🟡 條件) | 8KB | templates/betweencoffee_delivery/index.html |
| blobs.css (🟡 條件) | 32KB | templates/betweencoffee_delivery/index.html, templates/betweencoffee_delivery/landing_v3.html |
| fontawesome/css/all.css (🟢 全域) | 943KB | templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html |
| icomoon.css (🟢 全域) | 77KB | templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html |
| jquery.timepicker.min.css (🟢 全域) | 1KB | templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html |
| landing.css (🟡 條件) | 6KB | templates/betweencoffee_delivery/landing_v3.html |
| loyalty-table.css (🟡 條件) | 12KB | socialuser/templates/socialuser/loyalty_dashboard.html |
| magnific-popup.css (🟢 全域) | 6KB | templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html |
| owl.carousel.min.css (🟡 條件) | 4KB | templates/betweencoffee_delivery/index.html, templates/betweencoffee_delivery/landing_v3.html |
| owl.theme.default.min.css (🟡 條件) | 0KB | templates/betweencoffee_delivery/index.html, templates/betweencoffee_delivery/landing_v3.html |
| profile.css (🟡 條件) | 9KB | socialuser/templates/socialuser/profile.html |
| responsive-system.css (🟢 全域) | 4KB | templates/betweencoffee_delivery/base.html |
| select2.min.css (🟢 全域) | 15KB | templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html |
| staff_order_management.css (🟡 條件) | 35KB | templates/admin/staff_order_management.html |
| style-bootstrap.css (🟢 全域) | 92KB | templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html |
| style-custom.css (🟢 全域) | 36KB | templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html |
| style-utilities.css (🟢 全域) | 57KB | templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html |

## 🔴 死資產（未被任何模板引用，可清理）

- 無

## 🔴 死資產（非 .css：備份/源碼/垃圾）

`staff_order_management.css.bak`

## 🟡 重複引用（同 CSS 多模板載入）

- `animate-custom.css` ← templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html
- `bc-components.css` ← templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html
- `blobs.css` ← templates/betweencoffee_delivery/index.html, templates/betweencoffee_delivery/landing_v3.html
- `fontawesome/css/all.css` ← templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html
- `icomoon.css` ← templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html
- `jquery.timepicker.min.css` ← templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html
- `magnific-popup.css` ← templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html
- `owl.carousel.min.css` ← templates/betweencoffee_delivery/index.html, templates/betweencoffee_delivery/landing_v3.html
- `owl.theme.default.min.css` ← templates/betweencoffee_delivery/index.html, templates/betweencoffee_delivery/landing_v3.html
- `select2.min.css` ← templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html
- `style-bootstrap.css` ← templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html
- `style-custom.css` ← templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html
- `style-utilities.css` ← templates/admin/audit_log.html, templates/betweencoffee_delivery/base.html

## 🟡 外部 CSS（CDN / Google Fonts）

- `https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600;700&family=Noto+Sans+TC:wght@300;400;500;700&family=Mogra&display=swap`
- `https://fonts.googleapis.com/icon?family=Material+Icons`
- `https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined`
- `https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600;700&family=Noto+Sans+TC:wght@300;400;500;700&family=Mogra&display=block`
- `https://use.fontawesome.com/releases/v5.8.2/css/all.css`
- `https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap`
- `https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.5.0/css/bootstrap.min.css`
- `https://cdnjs.cloudflare.com/ajax/libs/mdbootstrap/4.19.1/css/mdb.min.css`

## HTTP 驗證

- ⚠️ 伺服器未運行（localhost:8081），HTTP 驗證略過（以檔案存在為準）
