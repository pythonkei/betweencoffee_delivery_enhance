#!/usr/bin/env node

/**
 * Simple Tavily Search MCP Server - Fixed Version
 * 提供 Tavily 搜索功能的 MCP 伺服器（修復版）
 */

// 使用直接路徑導入，避免 exports 配置問題
const { Server } = require('./node_modules/@modelcontextprotocol/sdk/dist/cjs/server/index.js');
const { StdioServerTransport } = require('./node_modules/@modelcontextprotocol/sdk/dist/cjs/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('./node_modules/@modelcontextprotocol/sdk/dist/cjs/types.js');
const axios = require('axios');

class TavilySearchServer {
  constructor() {
    this.server = new Server(
      {
        name: 'simple-tavily-search',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  setupToolHandlers() {
    // 列出可用工具
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'search_tavily',
            description: '使用 Tavily API 進行網絡搜索',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: '搜索查詢關鍵字',
                },
                max_results: {
                  type: 'number',
                  description: '最大結果數量 (1-10)',
                  default: 5,
                  minimum: 1,
                  maximum: 10,
                },
                include_answer: {
                  type: 'boolean',
                  description: '是否包含 AI 生成的答案',
                  default: true,
                },
                search_depth: {
                  type: 'string',
                  description: '搜索深度',
                  enum: ['basic', 'advanced'],
                  default: 'basic',
                },
              },
              required: ['query'],
            },
          },
        ],
      };
    });

    // 處理搜索工具請求
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'search_tavily':
            return await this.handleSearchTavily(args);
          default:
            throw new Error(`未知工具: ${name}`);
        }
      } catch (error) {
        console.error(`工具執行錯誤 (${name}):`, error);
        return {
          content: [
            {
              type: 'text',
              text: `錯誤: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async handleSearchTavily(args) {
    const {
      query,
      max_results = 5,
      include_answer = true,
      search_depth = 'basic',
    } = args;

    const apiKey = process.env.TAVILY_API_KEY;
    if (!apiKey) {
      throw new Error('TAVILY_API_KEY 環境變數未設置');
    }

    const response = await axios.post(
      'https://api.tavily.com/search',
      {
        api_key: apiKey,
        query,
        max_results,
        include_answer,
        search_depth,
      },
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000,
      }
    );

    const data = response.data;

    // 格式化結果
    const resultsText = data.results
      .map((result, index) => {
        return `**${index + 1}. ${result.title}**\n` +
               `網址: ${result.url}\n` +
               `相關度: ${(result.score * 100).toFixed(1)}%\n` +
               `內容: ${result.content.substring(0, 200)}...\n`;
      })
      .join('\n');

    const answerText = data.answer ? `\n**AI 答案:**\n${data.answer}\n` : '';

    return {
      content: [
        {
          type: 'text',
          text: `# Tavily 搜索結果: "${query}"\n\n` +
                `**搜索統計:**\n` +
                `- 查詢: ${data.query}\n` +
                `- 響應時間: ${data.response_time}秒\n` +
                `- 結果數量: ${data.results.length}\n` +
                `- 請求 ID: ${data.request_id}\n\n` +
                `**搜索結果:**\n${resultsText}` +
                answerText,
        },
      ],
    };
  }

  setupErrorHandling() {
    this.server.onerror = (error) => {
      console.error('MCP 伺服器錯誤:', error);
    };

    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Tavily Search MCP 伺服器已啟動 (stdio)');
  }
}

// 主程序
if (require.main === module) {
  const server = new TavilySearchServer();
  server.run().catch((error) => {
    console.error('伺服器啟動失敗:', error);
    process.exit(1);
  });
}

module.exports = { TavilySearchServer };