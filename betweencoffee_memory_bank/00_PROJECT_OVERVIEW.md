# 00_PROJECT_OVERVIEW

> **最後更新**: 2026-09-06（記憶庫瘦身補檔）
> **完整設定**: `betweencoffee_memory_bank/config/cline_config.json`

## 專案一句話
Between Coffee 咖啡店外帶網站與訂單製作管理系統：顧客下單 → 支付 → 製作佇列 → 取餐通知；含員工後台、積分/優惠券、社交登入。

## 技術棧
- 後端：Django 4.x、Django Channels（InMemoryChannelLayer）、PostgreSQL
- 前端：原生 HTML/CSS/JS + Bootstrap 5 + jQuery（黑金品牌視覺）
- 支付：PayPal、Alipay、FPS、現金
- 登入：django-allauth（Google / Facebook OAuth）
- 佈署：Render（Docker），DB＝Supabase PostgreSQL

## 核心模組
| 模組 | 職責 |
|------|------|
| `eshop` | 商品、訂單、支付、佇列（主要業務邏輯） |
| `cart` | 購物車 |
| `socialuser` | 社交登入、用戶資料 |
| `restaurant` | 員工、權限、製作端 |
| `core` | 工具與錯誤處理 |

## 線上
- Live：https://betweencoffee-delivery-enhance-v1.onrender.com/
- Repo：https://github.com/pythonkei/betweencoffee_delivery_enhance（公開，勿再 commit 機密）
