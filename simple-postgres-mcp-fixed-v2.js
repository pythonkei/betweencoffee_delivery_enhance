#!/usr/bin/env node

const { Client } = require('pg');

// PostgreSQL 連接配置函數
function createClient() {
  return new Client({
    connectionString: process.env.POSTGRES_URL || 'postgresql://postgres:111111@localhost:5432/betweencoffee_delivery_db',
    user: process.env.POSTGRES_USER || 'postgres',
    password: process.env.POSTGRES_PASSWORD || '111111',
    host: process.env.POSTGRES_HOST || 'localhost',
    port: process.env.POSTGRES_PORT || 5432,
    database: process.env.POSTGRES_DB || 'betweencoffee_delivery_db'
  });
}

// 簡單的 MCP 協議處理
async function handleMCP() {
  process.stdin.setEncoding('utf8');
  
  process.stdin.on('data', async (data) => {
    try {
      const request = JSON.parse(data.trim());
      
      if (request.method === 'initialize') {
        // 初始化響應
        const response = {
          jsonrpc: '2.0',
          id: request.id,
          result: {
            protocolVersion: '2024-11-05',
            capabilities: {
              tools: {},
              resources: {}
            },
            serverInfo: {
              name: 'simple-postgres-mcp',
              version: '1.0.0'
            }
          }
        };
        process.stdout.write(JSON.stringify(response) + '\n');
      }
      else if (request.method === 'tools/list') {
        // 工具列表響應
        const response = {
          jsonrpc: '2.0',
          id: request.id,
          result: {
            tools: [
              {
                name: 'execute_sql',
                description: '執行 SQL 查詢並返回結果',
                inputSchema: {
                  type: 'object',
                  properties: {
                    query: {
                      type: 'string',
                      description: '要執行的 SQL 查詢'
                    }
                  },
                  required: ['query']
                }
              },
              {
                name: 'list_tables',
                description: '列出數據庫中的所有表',
                inputSchema: {
                  type: 'object',
                  properties: {}
                }
              },
              {
                name: 'get_table_info',
                description: '獲取表的詳細信息',
                inputSchema: {
                  type: 'object',
                  properties: {
                    table_name: {
                      type: 'string',
                      description: '表名'
                    }
                  },
                  required: ['table_name']
                }
              }
            ]
          }
        };
        process.stdout.write(JSON.stringify(response) + '\n');
      }
      else if (request.method === 'tools/call') {
        // 工具調用處理
        const { name, arguments: args } = request.params;
        const client = createClient();
        
        try {
          await client.connect();
          
          let result;
          switch (name) {
            case 'execute_sql':
              const { query } = args;
              const sqlResult = await client.query(query);
              result = {
                content: [
                  {
                    type: 'text',
                    text: JSON.stringify({
                      rows: sqlResult.rows,
                      rowCount: sqlResult.rowCount,
                      fields: sqlResult.fields.map(f => ({ name: f.name, dataTypeID: f.dataTypeID }))
                    }, null, 2)
                  }
                ]
              };
              break;
              
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
              result = {
                content: [
                  {
                    type: 'text',
                    text: JSON.stringify(tablesResult.rows, null, 2)
                  }
                ]
              };
              break;
              
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
              result = {
                content: [
                  {
                    type: 'text',
                    text: JSON.stringify(tableInfoResult.rows, null, 2)
                  }
                ]
              };
              break;
              
            default:
              throw new Error(`未知的工具: ${name}`);
          }
          
          const response = {
            jsonrpc: '2.0',
            id: request.id,
            result: result
          };
          process.stdout.write(JSON.stringify(response) + '\n');
        } catch (error) {
          const response = {
            jsonrpc: '2.0',
            id: request.id,
            error: {
              code: -32603,
              message: `執行錯誤: ${error.message}`
            }
          };
          process.stdout.write(JSON.stringify(response) + '\n');
        } finally {
          await client.end();
        }
      }
      else if (request.method === 'resources/list') {
        // 資源列表 - 返回空列表，因為我們不支持資源
        const response = {
          jsonrpc: '2.0',
          id: request.id,
          result: {
            resources: []
          }
        };
        process.stdout.write(JSON.stringify(response) + '\n');
      }
      else if (request.method === 'resources/templates/list') {
        // 資源模板列表 - 返回空列表
        const response = {
          jsonrpc: '2.0',
          id: request.id,
          result: {
            resourceTemplates: []
          }
        };
        process.stdout.write(JSON.stringify(response) + '\n');
      }
      else {
        // 未知方法
        const response = {
          jsonrpc: '2.0',
          id: request.id,
          error: {
            code: -32601,
            message: `方法未找到: ${request.method}`
          }
        };
        process.stdout.write(JSON.stringify(response) + '\n');
      }
    } catch (error) {
      // JSON 解析錯誤或其他錯誤
      const response = {
        jsonrpc: '2.0',
        id: null,
        error: {
          code: -32700,
          message: `解析錯誤: ${error.message}`
        }
      };
      process.stdout.write(JSON.stringify(response) + '\n');
    }
  });
  
  // 處理 stdin 結束
  process.stdin.on('end', () => {
    process.exit(0);
  });
}

// 啟動伺服器
console.error('Simple PostgreSQL MCP 伺服器已啟動 (v2 - 修復客戶端重用問題)');
handleMCP().catch(error => {
  console.error('伺服器錯誤:', error);
  process.exit(1);
});