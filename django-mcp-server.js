#!/usr/bin/env node
/**
 * Django MCP Server - Between Coffee 訂單管理系統
 *
 * 提供 Django 管理相關的 MCP 工具：
 *  - django_run_command        : 執行 Django management command
 *  - django_order_info         : 查詢訂單資訊（by order_id）
 *  - django_queue_status       : 查詢製作隊列狀態
 *  - django_recent_orders      : 查詢最近訂單
 *
 * 透過 child_process 呼叫 manage.py shell -c 執行查詢。
 */

const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

// SDK exports 攔截 bare specifier，改用絕對路徑繞過
const SDK_DIR = path.join(__dirname, "node_modules", "@modelcontextprotocol", "sdk", "dist", "cjs");
const { McpServer } = require(path.join(SDK_DIR, "server", "mcp.js"));
const { StdioServerTransport } = require(path.join(SDK_DIR, "server", "stdio.js"));
const { z } = require(path.join(__dirname, "node_modules", "zod"));

// ===== 環境變數 =====
const PROJECT_DIR = process.env.DJANGO_PROJECT_DIR || process.cwd();
const PYTHON = process.env.PYTHON_EXECUTABLE || "python";

// ===== 工具函數 =====
function runDjango(code, { timeout = 30000, cwd = PROJECT_DIR } = {}) {
  const script = `
import json, sys
try:
    import django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
    django.setup()
    result = ${code}
    print('__BC_MCP_RESULT__' + json.dumps(result, ensure_ascii=False, default=str))
except Exception as e:
    print('__BC_MCP_ERROR__' + str(e), file=sys.stderr)
    sys.exit(1)
`;
  const res = spawnSync(PYTHON, ["manage.py", "shell", "-c", script], {
    cwd,
    timeout,
    encoding: "utf-8",
    env: process.env,
  });
  if (res.error) {
    return { success: false, message: `執行失敗: ${res.error.message}` };
  }
  const stdout = res.stdout || "";
  const stderr = res.stderr || "";
  const marker = stdout.indexOf("__BC_MCP_RESULT__");
  if (marker !== -1) {
    try {
      return { success: true, data: JSON.parse(stdout.slice(marker + "__BC_MCP_RESULT__".length)) };
    } catch (e) {
      return { success: false, message: `JSON 解析失敗: ${e.message}` };
    }
  }
  const errMarker = stderr.indexOf("__BC_MCP_ERROR__");
  if (errMarker !== -1) {
    return { success: false, message: stderr.slice(errMarker + "__BC_MCP_ERROR__".length) };
  }
  return { success: false, message: `無預期輸出\nSTDOUT: ${stdout}\nSTDERR: ${stderr}` };
}

function result(content) {
  return {
    content: [{ type: "text", text: typeof content === "string" ? content : JSON.stringify(content, null, 2) }],
  };
}

function error(message) {
  return {
    isError: true,
    content: [{ type: "text", text: String(message) }],
  };
}

// ===== 建立 MCP Server =====
const server = new McpServer({
  name: "django-manager",
  version: "1.0.0",
});

// ---- 1. 執行 Django management command ----
server.tool(
  "django_run_command",
  "執行 Django management command（如: cleanup_queue, debug_queue, validate_pickup_codes 等）",
  {
    command: z.string().describe("要執行的 management command 名稱"),
    args: z.array(z.string()).optional().describe("傳給 command 的參數"),
  },
  async ({ command, args = [] }) => {
    try {
      const res = spawnSync(PYTHON, ["manage.py", command, ...args], {
        cwd: PROJECT_DIR,
        timeout: 60000,
        encoding: "utf-8",
        env: process.env,
      });
      if (res.error) return error(`執行失敗: ${res.error.message}`);
      return result({
        exitCode: res.status,
        stdout: (res.stdout || "").slice(-4000),
        stderr: (res.stderr || "").slice(-1000),
      });
    } catch (e) {
      return error(String(e));
    }
  }
);

// ---- 2. 查詢訂單資訊 ----
server.tool(
  "django_order_info",
  "查詢訂單詳細資訊（訂單狀態、支付狀態、金額、商品等）",
  {
    order_id: z.number().int().positive().describe("訂單 ID"),
  },
  async ({ order_id }) => {
    try {
      const res = runDjango(`
{
    'id': o.id,
    'order_number': o.order_number or '',
    'status': o.status,
    'payment_status': o.payment_status,
    'payment_method': o.payment_method,
    'total_price': str(o.total_price),
    'original_total_price': str(o.original_total_price or 0),
    'pickup_code': o.pickup_code,
    'contact_name': o.contact_name or '',
    'phone': o.phone or '',
    'created_at': o.created_at.isoformat() if o.created_at else '',
    'updated_at': o.updated_at.isoformat() if o.updated_at else '',
    'is_quick_order': o.is_quick_order,
    'item_count': len(o.get_items()) if hasattr(o, 'get_items') else 0,
} if (o := __import__('eshop.models', fromlist=['OrderModel']).OrderModel.objects.filter(id=${order_id}).first())
  else {'error': f'訂單 ${order_id} 不存在'}
`);
      if (!res.success) return error(res.message);
      return result(res.data);
    } catch (e) {
      return error(String(e));
    }
  }
);

// ---- 3. 查詢製作隊列狀態 ----
server.tool(
  "django_queue_status",
  "查詢當前製作隊列狀態（等待/製作中/就緒的訂單）",
  {},
  async () => {
    try {
      const res = runDjango(`
import json
from eshop.models import CoffeeQueue
queue_items = CoffeeQueue.objects.select_related('order').order_by('queue_position')[:20]
[{'id': q.id, 'queue_position': q.queue_position, 'status': q.status,
  'coffee_count': q.coffee_count, 'order_id': q.order_id,
  'order_status': q.order.status if q.order else None,
  'pickup_code': q.order.pickup_code if q.order else None,
  'added_at': q.added_at.isoformat() if q.added_at else None} for q in queue_items]
`);
      if (!res.success) return error(res.message);
      return result({ total: Array.isArray(res.data) ? res.data.length : 0, items: res.data });
    } catch (e) {
      return error(String(e));
    }
  }
);

// ---- 4. 查詢最近訂單 ----
server.tool(
  "django_recent_orders",
  "查詢最近 N 筆訂單（預設 10 筆）",
  {
    limit: z.number().int().min(1).max(50).optional().describe("要查詢的筆數（預設 10）"),
    status: z.string().optional().describe("依訂單狀態過濾（pending/waiting/preparing/ready/completed）"),
  },
  async ({ limit = 10, status = null }) => {
    try {
      const filter = status ? `, status='${status}'` : "";
      const res = runDjango(`
from eshop.models import OrderModel
qs = OrderModel.objects.all()${filter}.order_by('-created_at')[:${limit}]
[{'id': o.id, 'order_number': o.order_number or '', 'status': o.status,
  'payment_status': o.payment_status, 'total_price': str(o.total_price),
  'pickup_code': o.pickup_code, 'created_at': o.created_at.isoformat() if o.created_at else ''} for o in qs]
`);
      if (!res.success) return error(res.message);
      return result({ count: Array.isArray(res.data) ? res.data.length : 0, orders: res.data });
    } catch (e) {
      return error(String(e));
    }
  }
);

// ===== 啟動 =====
async function main() {
  if (!fs.existsSync(path.join(PROJECT_DIR, "manage.py"))) {
    process.stderr.write(`[django-manager] 警告: 找不到 manage.py (${PROJECT_DIR})\n`);
  }
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((e) => {
  process.stderr.write(`[django-manager] 啟動失敗: ${e.message}\n`);
  process.exit(1);
});