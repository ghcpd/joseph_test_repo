const http = require('http');
const fs = require('fs');
const path = require('path');

const publicDir = path.join(__dirname, 'public');
const port = process.env.PORT || 3000;

const server = http.createServer((req, res) => {
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
