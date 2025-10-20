#!/usr/bin/env node
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { registerGetMotokoContext } from './tools/get-motoko-context.tool.js'
import { registerGenerateMotokoCode } from './tools/generate-motoko-code.tool.js'

const PACKAGE_NAME = 'icp-coder-mcp-server'
const VERSION = '0.1.1'
const API_KEY_ENV = 'API_KEY'
const API_KEY_FLAG = '--api-key'
const BACKEND_URL_ENV = 'BACKEND_URL'
const DEFAULT_BACKEND_BASE_URL =
  process.env.PROD_BACKEND_URL || 'http://localhost:8080'

type StartOptions = {
  apiKey?: string
  backendBaseUrl?: string
}

async function start(options: StartOptions = {}) {
  const apiKey = options.apiKey ?? resolveApiKeyFromProcess()
  const backendBaseUrl = options.backendBaseUrl ?? resolveBackendBaseUrlFromProcess()
  if (!apiKey)
    throw new Error(`API key is required. Set ${API_KEY_ENV} or pass ${API_KEY_FLAG}=<key>.`)
  const server = new McpServer({ name: PACKAGE_NAME, version: VERSION })
  registerGetMotokoContext(server, { apiKey, baseUrl: backendBaseUrl })
  registerGenerateMotokoCode(server, { apiKey, baseUrl: backendBaseUrl })
  const transport = new StdioServerTransport()
  console.error(`[${PACKAGE_NAME}] starting MCP server (v${VERSION}) on stdio...`)
  await server.connect(transport)
  console.error(`[${PACKAGE_NAME}] STDIO transport ready`)
  setupGracefulShutdown(server, transport)
  return { server, transport }
}

function resolveApiKeyFromProcess(): string | undefined {
  const fromEnv = process.env[API_KEY_ENV]
  if (fromEnv?.trim()) return fromEnv.trim()
  const args = process.argv.slice(2)
  for (let i = 0; i < args.length; i++) {
    const arg = args[i]
    if (!arg.startsWith(API_KEY_FLAG)) continue
    if (arg === API_KEY_FLAG) return args[i + 1]?.trim()
    const [, val] = arg.split('=')
    if (val?.length) return val.trim()
  }
  return undefined
}

function resolveBackendBaseUrlFromProcess(): string {
  const fromEnv = process.env[BACKEND_URL_ENV]
  return fromEnv?.trim() || DEFAULT_BACKEND_BASE_URL
}

function setupGracefulShutdown(server: McpServer, transport: StdioServerTransport) {
  const shutdown = async (signal?: NodeJS.Signals) => {
    console.error(`[${PACKAGE_NAME}] Shutting down${signal ? ` after ${signal}` : ''}`)
    await Promise.allSettled([
      (async () => typeof transport.close === 'function' && (await transport.close()))(),
      (async () => typeof server.close === 'function' && (await server.close()))(),
    ])
    process.exit(0)
  }
  for (const s of ['SIGINT', 'SIGTERM'] as const)
    process.once(s, () => void shutdown(s))
}

start().catch((err) => {
  console.error(`[${PACKAGE_NAME}] Fatal error:`, err)
  process.exit(1)
})

export { start, type StartOptions }
