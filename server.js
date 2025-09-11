const http = require('http');
const fs = require('fs');
const path = require('path');

const publicDir = path.join(__dirname, 'public');
const port = process.env.PORT || 3000;

const server = http.createServer(async (req, res) => {
  if (req.url.startsWith('/api/')) {
    // Simple proxy for GitHub API: /api/repos/:owner/:repo/:resource
    try {
      const [, , , owner, repo, resource] = req.url.split(/[/?]/);
      const search = req.url.includes('?') ? '?' + req.url.split('?')[1] : '';
      if (!owner || !repo || !['pulls', 'issues'].includes(resource)) {
        res.writeHead(400);
        res.end('Bad request');
        return;
      }
      const target = `https://api.github.com/repos/${owner}/${repo}/${resource}${search}`;
      const gh = await fetch(target, { headers: { 'Accept': 'application/vnd.github+json', 'User-Agent': 'ghcpd-repo-viewer' } });
      if (gh.status === 403) {
        const samplePath = path.join(publicDir, `sample-${resource}.json`);
        if (fs.existsSync(samplePath)) {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          return res.end(fs.readFileSync(samplePath));
        }
      }
      const data = await gh.text();
      res.writeHead(gh.status, { 'Content-Type': 'application/json' });
      res.end(data);
      return;
    } catch (e) {
      res.writeHead(500);
      res.end('Proxy error');
      return;
    }
  }

  let filePath = req.url === '/' ? path.join(publicDir, 'index.html') : path.join(publicDir, req.url);
  const ext = path.extname(filePath).toLowerCase();
  const mime = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json'
  }[ext] || 'text/plain';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }
    res.writeHead(200, { 'Content-Type': mime });
    res.end(content);
  });
});

server.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
