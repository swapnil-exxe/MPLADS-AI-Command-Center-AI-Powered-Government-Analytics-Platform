/**
 * MPLADS AI Command Center — Node.js Express Server Entrypoint
 * Spawns Python FastAPI backend on sub-port and proxies API traffic
 * Serves React SPA single-page frontend application
 */

const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 8000;
const PYTHON_PORT = process.env.PYTHON_PORT || 8001;

// Global CORS
app.use(cors());

// 1. Spawn Python FastAPI Subservice
console.log(`[Node.js Server] Spawning Python Uvicorn subservice on port ${PYTHON_PORT}...`);
const pythonProcess = spawn('python3', [
  '-m', 'uvicorn', 'api.main:app',
  '--host', '127.0.0.1',
  '--port', String(PYTHON_PORT)
], {
  cwd: __dirname,
  env: { ...process.env, PYTHONPATH: __dirname }
});

pythonProcess.stdout.on('data', (data) => {
  console.log(`[FastAPI] ${data.toString().trim()}`);
});

pythonProcess.stderr.on('data', (data) => {
  console.error(`[FastAPI Error] ${data.toString().trim()}`);
});

pythonProcess.on('close', (code) => {
  console.log(`[Node.js Server] Python subservice exited with code ${code}`);
});

// 2. HTTP Proxy Setup for FastAPI Endpoints (Mounted BEFORE body parsers to prevent POST stream drain)
let httpProxy;
try {
  httpProxy = require('http-proxy-middleware');
} catch (e) {
  console.warn('[Node.js Server] http-proxy-middleware not installed, fallback to direct routing.');
}

if (httpProxy && httpProxy.createProxyMiddleware) {
  const apiProxy = httpProxy.createProxyMiddleware({
    target: `http://127.0.0.1:${PYTHON_PORT}`,
    changeOrigin: true,
  });

  app.use('/api', apiProxy);
  app.use('/v1', apiProxy);
  app.use('/docs', apiProxy);
  app.use('/openapi.json', apiProxy);
}

// 3. Express Body Parsers for local Node routes only
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 4. Serve Frontend Production Build Artifacts
const frontendDist = path.join(__dirname, '../frontend/dist');
const localDist = path.join(__dirname, 'dist');

const staticDir = require('fs').existsSync(frontendDist) ? frontendDist : localDist;
app.use(express.static(staticDir));

app.get('/health', (req, res) => {
  res.json({ status: 'ok', server: 'Node.js Express Gateway', port: PORT });
});

app.get('*', (req, res) => {
  const indexPath = path.join(staticDir, 'index.html');
  if (require('fs').existsSync(indexPath)) {
    res.sendFile(indexPath);
  } else {
    res.json({
      status: 'healthy',
      message: 'MPLADS AI Command Center Express Gateway operational',
      backend: `http://127.0.0.1:${PYTHON_PORT}/api/v1`
    });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 MPLADS Command Center listening on http://0.0.0.0:${PORT}`);
});
