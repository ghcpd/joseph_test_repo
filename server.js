import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildApiUrl } from './src/github.js';

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const publicDir = path.join(__dirname, 'public');
const serverPort = process.env.PORT ? Number(process.env.PORT) : 4173;

const mimeTypes = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

function sendJson(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  });
  res.end(body);
}

async function handleApiRequest(req, res, url) {
  if (req.method === 'OPTIONS') {
    sendJson(res, 204, {});
    return;
  }

  const owner = url.searchParams.get('owner');
  const repo = url.searchParams.get('repo');
  const type = url.searchParams.get('type');

  if (!owner || !repo || !type) {
    sendJson(res, 400, { error: 'Missing required query parameters: owner, repo, type.' });
    return;
  }

  try {
    console.log(`Proxying ${owner}/${repo} (${type})`);
    const upstreamUrl = buildApiUrl(owner, repo, type);
    const response = await fetch(upstreamUrl, {
      headers: {
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
      }
    });

    const data = await response.json();

    if (!response.ok) {
      const message = data && data.message ? data.message : `GitHub API responded with status ${response.status}.`;
      sendJson(res, response.status, { error: message });
      return;
    }

    sendJson(res, 200, data);
  } catch (error) {
    console.error('Proxy request failed:', error);
    sendJson(res, 500, { error: 'Failed to contact GitHub API.' });
  }
}

function serveStaticFile(res, filePath) {
  fs.readFile(filePath, (error, content) => {
    if (error) {
      if (error.code === 'ENOENT') {
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('Not found');
        return;
      }

      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Internal server error');
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(content);
  });
}

function handleRequest(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (url.pathname === '/api/github') {
    handleApiRequest(req, res, url);
    return;
  }

  let safePath = decodeURIComponent(url.pathname);
  let baseDir = publicDir;

  if (safePath.startsWith('/src/')) {
    baseDir = path.join(__dirname, 'src');
    safePath = safePath.replace(/^\/src/, '');
  } else if (safePath === '/' || safePath === '') {
    safePath = '/index.html';
  }

  const normalizedPath = path.normalize(safePath).replace(/^\/+/, '');
  const filePath = path.join(baseDir, normalizedPath);

  if (!filePath.startsWith(baseDir)) {
    res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Access denied');
    return;
  }

  serveStaticFile(res, filePath);
}

const server = http.createServer(handleRequest);

server.listen(serverPort, () => {
  console.log(`Server started at http://localhost:${serverPort}`);
});
