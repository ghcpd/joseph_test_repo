const express = require('express');
const fetch = require('node-fetch');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(__dirname));

function authHeaders() {
  const headers = { 'User-Agent': 'gh-proxy-app' };
  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `token ${process.env.GITHUB_TOKEN}`;
  }
  return headers;
}

async function proxyGithub(res, url) {
  try {
    const ghRes = await fetch(url, { headers: authHeaders() });
    const remaining = ghRes.headers.get('x-ratelimit-remaining');
    const reset = ghRes.headers.get('x-ratelimit-reset');

    if (ghRes.status === 403 && remaining === '0') {
      return res.status(429).json({ error: 'GitHub API rate limit exceeded', reset: reset ? new Date(parseInt(reset, 10) * 1000) : null });
    }

    if (!ghRes.ok) {
      const text = await ghRes.text();
      return res.status(ghRes.status).json({ error: `GitHub API error: ${ghRes.status}`, details: text });
    }

    const data = await ghRes.json();
    return res.json(data);
  } catch (err) {
    return res.status(500).json({ error: 'Server error', details: String(err) });
  }
}

app.get('/api/prs', async (req, res) => {
  const repo = req.query.repo;
  if (!repo || !/^[^/]+\/[^/]+$/.test(repo)) {
    return res.status(400).json({ error: 'Invalid repo format. Expected owner/repo' });
  }
  const url = `https://api.github.com/repos/${repo}/pulls?state=all&per_page=30`;
  return proxyGithub(res, url);
});

app.get('/api/issues', async (req, res) => {
  const repo = req.query.repo;
  if (!repo || !/^[^/]+\/[^/]+$/.test(repo)) {
    return res.status(400).json({ error: 'Invalid repo format. Expected owner/repo' });
  }
  const url = `https://api.github.com/repos/${repo}/issues?state=all&per_page=30`;
  return proxyGithub(res, url);
});

app.get('/api/pr', async (req, res) => {
  const repo = req.query.repo;
  const number = req.query.number;
  if (!repo || !/^[^/]+\/[^/]+$/.test(repo)) {
    return res.status(400).json({ error: 'Invalid repo format. Expected owner/repo' });
  }
  if (!number || !/^[0-9]+$/.test(number)) {
    return res.status(400).json({ error: 'Invalid PR number' });
  }
  const url = `https://api.github.com/repos/${repo}/pulls/${number}`;
  return proxyGithub(res, url);
});

app.get('/api/issue', async (req, res) => {
  const repo = req.query.repo;
  const number = req.query.number;
  if (!repo || !/^[^/]+\/[^/]+$/.test(repo)) {
    return res.status(400).json({ error: 'Invalid repo format. Expected owner/repo' });
  }
  if (!number || !/^[0-9]+$/.test(number)) {
    return res.status(400).json({ error: 'Invalid issue number' });
  }
  const url = `https://api.github.com/repos/${repo}/issues/${number}`;
  return proxyGithub(res, url);
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
