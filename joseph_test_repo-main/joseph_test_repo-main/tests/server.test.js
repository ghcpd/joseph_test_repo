const test = require('node:test');
const assert = require('node:assert');
const http = require('node:http');
const app = require('../server');

let server;
let baseUrl;

test.before(async () => {
  server = http.createServer(app);
  await new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      baseUrl = `http://127.0.0.1:${port}`;
      resolve();
    });
  });
});

test.after(async () => {
  if (server) {
    await new Promise((resolve, reject) => {
      server.close((err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }
});

test('rejects invalid repo parameter', async () => {
  const response = await fetch(`${baseUrl}/api/prs?repo=not-a-valid-repo`);
  assert.strictEqual(response.status, 400);
  const body = await response.json();
  assert.ok(body.error.includes('Invalid repository'));
});

test('returns data for a valid repository (issues)', async () => {
  const response = await fetch(`${baseUrl}/api/issues?repo=octocat/Hello-World`);
  assert.strictEqual(response.status, 200);
  const body = await response.json();
  assert.ok(Array.isArray(body.items));
});

test('surfaces GitHub error for missing repository', async () => {
  const response = await fetch(`${baseUrl}/api/prs?repo=octocat/Definitely-Not-A-Repo`);
  assert.strictEqual(response.status, 500);
  const body = await response.json();
  assert.ok(/GitHub API error/i.test(body.error) || /rate limit/i.test(body.error));
});