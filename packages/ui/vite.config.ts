import { defineConfig, Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import { execSync } from 'child_process'
import path from 'path'
import fs from 'fs'

function zforgeApiPlugin(): Plugin {
  const handler = (server: any) => {
    const rootDir = path.resolve(__dirname, '../..')
    const reportsDir = path.join(rootDir, 'workspace/synthetic-banking/reports')
    const scriptPath = path.join(__dirname, 'run_workflow.py')

    server.middlewares.use((req: any, res: any, next: any) => {
      const rawUrl = req.url || ''
      console.log('[Vite Middleware URL]:', rawUrl)
      const url = rawUrl.split('?')[0]

      // Static /reports/* files (AFP editor, JSON report, PPFA)
      if (url.startsWith('/reports/')) {
        const reqPath = url.substring('/reports/'.length)
        const filePath = path.join(reportsDir, reqPath)
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
          const ext = path.extname(filePath).toLowerCase()
          const mimeTypes: Record<string, string> = {
            '.html': 'text/html; charset=utf-8',
            '.svg': 'image/svg+xml',
            '.json': 'application/json',
            '.ppfa': 'text/plain; charset=utf-8',
          }
          res.setHeader('Content-Type', mimeTypes[ext] || 'text/plain')
          res.end(fs.readFileSync(filePath))
          return
        }
      }

      // Live /api/workflow execution
      if (url === '/api/workflow' || url === '/api/workflow/') {
        res.setHeader('Content-Type', 'application/json')
        res.setHeader('Access-Control-Allow-Origin', '*')

        try {
          const cmd = `uv run --project packages/engine python "${scriptPath}"`
          const output = execSync(cmd, {
            cwd: rootDir,
            encoding: 'utf-8',
            maxBuffer: 10 * 1024 * 1024,
          })

          const lines = output.trim().split('\n')
          const jsonLine = lines[lines.length - 1]
          res.end(jsonLine)
        } catch (err: any) {
          const evPath = path.join(reportsDir, 'tamper-evident-evidence.json')
          if (fs.existsSync(evPath)) {
            res.end(fs.readFileSync(evPath, 'utf-8'))
          } else {
            res.statusCode = 500
            res.end(JSON.stringify({ error: err.message }))
          }
        }
        return
      }

      next()
    })
  }

  return {
    name: 'zforge-api-plugin',
    configureServer(server) {
      handler(server)
    },
    configurePreviewServer(server) {
      handler(server)
    },
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), zforgeApiPlugin()],
  server: {
    port: 5173,
    host: '0.0.0.0',
  },
})
