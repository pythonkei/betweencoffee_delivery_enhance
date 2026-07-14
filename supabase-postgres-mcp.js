#!/usr/bin/env node
/**
 * Simple PostgreSQL MCP Server (Fixed v2)
 * Connects to PostgreSQL using POSTGRES_URL env var and provides query tools.
 */
const { Pool } = require('pg');

// --- Config ---
const connectionString = process.env.POSTGRES_URL;
if (!connectionString) {
    console.error('POSTGRES_URL environment variable is required');
    process.exit(1);
}

const pool = new Pool({ connectionString, max: 3 });

// --- MCP Protocol via stdio ---
const readline = require('readline');
const rl = readline.createInterface({ input: process.stdin });

function sendResponse(id, result) {
    const response = JSON.stringify({ jsonrpc: '2.0', id, result });
    process.stdout.write(response + '\n');
}

function sendError(id, code, message) {
    const response = JSON.stringify({ jsonrpc: '2.0', id, error: { code, message } });
    process.stdout.write(response + '\n');
}

async function handleRequest(request) {
    const { id, method, params } = request;
    try {
        switch (method) {
            case 'initialize':
                sendResponse(id, {
                    protocolVersion: '2024-11-05',
                    capabilities: { tools: {} },
                    serverInfo: { name: 'simple-postgres', version: '2.0.0' }
                });
                break;

            case 'tools/list':
                sendResponse(id, {
                    tools: [
                        {
                            name: 'query',
                            description: 'Execute a read-only SQL query against the PostgreSQL database',
                            inputSchema: {
                                type: 'object',
                                properties: {
                                    sql: { type: 'string', description: 'The SQL query to execute (read-only)' }
                                },
                                required: ['sql']
                            }
                        },
                        {
                            name: 'list_tables',
                            description: 'List all tables in the database',
                            inputSchema: { type: 'object', properties: {} }
                        },
                        {
                            name: 'describe_table',
                            description: 'Describe the schema of a table',
                            inputSchema: {
                                type: 'object',
                                properties: {
                                    table: { type: 'string', description: 'Table name' }
                                },
                                required: ['table']
                            }
                        }
                    ]
                });
                break;

            case 'tools/call':
                const { name, arguments: args } = params;
                if (name === 'query') {
                    const result = await pool.query(args.sql);
                    sendResponse(id, {
                        content: [{ type: 'text', text: JSON.stringify(result.rows, null, 2) }]
                    });
                } else if (name === 'list_tables') {
                    const result = await pool.query(
                        "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema') ORDER BY table_schema, table_name"
                    );
                    sendResponse(id, {
                        content: [{ type: 'text', text: JSON.stringify(result.rows, null, 2) }]
                    });
                } else if (name === 'describe_table') {
                    const result = await pool.query(
                        'SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name = $1 ORDER BY ordinal_position',
                        [args.table]
                    );
                    sendResponse(id, {
                        content: [{ type: 'text', text: JSON.stringify(result.rows, null, 2) }]
                    });
                } else {
                    sendError(id, -32601, `Unknown tool: ${name}`);
                }
                break;

            case 'notifications/initialized':
                // No response needed for notifications
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
        const request = JSON.parse(line);
        handleRequest(request);
    } catch (e) {
        console.error('Failed to parse request:', e.message);
    }
});

process.on('SIGTERM', () => { pool.end(); process.exit(0); });
process.on('SIGINT', () => { pool.end(); process.exit(0); });
