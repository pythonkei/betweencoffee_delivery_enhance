#!/usr/bin/env node

const { Client } = require('pg');
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');

// PostgreSQL 連接配置
const client = new Client({
  connectionString: process.env.POSTGRES_URL || 'postgresql://postgres:111111@localhost:5432/betweencoffee_delivery_db',
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || '111111',
  host: process.env.POSTGRES_HOST || 'localhost',
  port: process.env.POSTGRES_PORT || 5432,
  database: process.env.POSTGRES_DB || 'betweencoffee_delivery_db'
});

// 創建 MCP 伺服器
const server = new Server(
  {
    name: 'simple-postgres-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// 工具定義
const tools = {
  execute_sql: {
    name: 'execute_sql',
    description: '執行 SQL 查詢並返回結果',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: '要執行的 SQL 查詢',
        },
      },
      required: ['query'],
    },
  },
  list_tables: {
    name: 'list_tables',
    description: '列出數據庫中的所有表',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  get_table_info: {
    name: 'get_table_info',
    description: '獲取表的詳細信息',
    inputSchema: {
      type: 'object',
      properties: {
        table_name: {
          type: 'string',
          description: '表名',
        },
      },
      required: ['table_name'],
    },
  },
  count_records: {
    name: 'count_records',
    description: '計算表中的記錄數',
    inputSchema: {
      type: 'object',
      properties: {
        table_name: {
          type: 'string',
          description: '表名',
        },
      },
      required: ['table_name'],
    },
  },
};

// 設置工具處理程序
server.setRequestHandler('tools/list', async () => ({
  tools: Object.values(tools),
}));

server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    await client.connect();
    
    switch (name) {
      case 'execute_sql':
        const { query } = args;
        const result = await client.query(query);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                rows: result.rows,
                rowCount: result.rowCount,
                fields: result.fields.map(f => ({ name: f.name, dataTypeID: f.dataTypeID })),
              }, null, 2),
            },
          ],
        };
        
      case 'list_tables':
        const tablesResult = await client.query(`
          SELECT 
            table_schema,
            table_name,
            table_type
          FROM information_schema.tables 
          WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
          ORDER BY table_schema, table_name
        `);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(tablesResult.rows, null, 2),
            },
          ],
        };
        
      case 'get_table_info':
        const { table_name } = args;
        const tableInfoResult = await client.query(`
          SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
          FROM information_schema.columns 
          WHERE table_name = $1
          ORDER BY ordinal_position
        `, [table_name]);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(tableInfoResult.rows, null, 2),
            },
          ],
        };
        
      case 'count_records':
        const { table_name: countTable } = args;
        const countResult = await client.query(`SELECT COUNT(*) as count FROM ${countTable}`);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({ count: parseInt(countResult.rows[0].count) }, null, 2),
            },
          ],
        };
        
      default:
        throw new Error(`未知的工具: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `錯誤: ${error.message}`,
        },
      ],
      isError: true,
    };
  } finally {
    await client.end();
  }
});

// 啟動伺服器
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Simple PostgreSQL MCP 伺服器已啟動');
}

main().catch((error) => {
  console.error('伺服器錯誤:', error);
  process.exit(1);
});