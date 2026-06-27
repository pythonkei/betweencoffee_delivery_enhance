#!/usr/bin/env node
/**
 * Simple Tavily Search MCP Server (Fixed)
 * Provides web search via Tavily API.
 */
const https = require('https');

// --- Config ---
const API_KEY = process.env.TAVILY_API_KEY;
if (!API_KEY) {
    console.error('TAVILY_API_KEY environment variable is required');
    process.exit(1);
}
const TAVILY_URL = 'api.tavily.com';

function tavilyRequest(endpoint, data) {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify({ ...data, api_key: API_KEY });
        const options = {
            hostname: TAVILY_URL,
            path: endpoint,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            }
        };
        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => { body += chunk; });
            res.on('end', () => {
                try {
                    resolve(JSON.parse(body));
                } catch (e) {
                    reject(new Error(`Failed to parse response: ${body.substring(0, 200)}`));
                }
            });
        });
        req.on('error', reject);
        req.write(postData);
        req.end();
    });
}

// --- MCP Protocol via stdio ---
const readline = require('readline');
const rl = readline.createInterface({ input: process.stdin });

function sendResponse(id, result) {
    process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id, result }) + '\n');
}

function sendError(id, code, message) {
    process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id, error: { code, message } }) + '\n');
}

async function handleRequest(request) {
    const { id, method, params } = request;
    try {
        switch (method) {
            case 'initialize':
                sendResponse(id, {
                    protocolVersion: '2024-11-05',
                    capabilities: { tools: {} },
                    serverInfo: { name: 'simple-tavily-search', version: '1.0.0' }
                });
                break;

            case 'tools/list':
                sendResponse(id, {
                    tools: [
                        {
                            name: 'search',
                            description: 'Search the web using Tavily API',
                            inputSchema: {
                                type: 'object',
                                properties: {
                                    query: { type: 'string', description: 'Search query' },
                                    max_results: { type: 'number', description: 'Max results (default 5)', default: 5 }
                                },
                                required: ['query']
                            }
                        }
                    ]
                });
                break;

            case 'tools/call':
                const { name, arguments: args } = params;
                if (name === 'search') {
                    const result = await tavilyRequest('/search', {
                        query: args.query,
                        max_results: args.max_results || 5,
                        search_depth: 'basic'
                    });
                    const formatted = (result.results || []).map((r, i) =>
                        `${i + 1}. ${r.title}\n   URL: ${r.url}\n   ${r.content}`
                    ).join('\n\n') || 'No results found';
                    sendResponse(id, {
                        content: [{ type: 'text', text: formatted }]
                    });
                } else {
                    sendError(id, -32601, `Unknown tool: ${name}`);
                }
                break;

            case 'notifications/initialized':
                break;

            default:
                sendError(id, -32601, `Unknown method: ${method}`);
        }
    } catch (err) {
        sendError(id, -32000, err.message);
    }
}

rl.on('line', (line) => {
    try {
        handleRequest(JSON.parse(line));
    } catch (e) {
        console.error('Failed to parse request:', e.message);
    }
});
