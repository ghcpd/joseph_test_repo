const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Simple in-memory cache to limit API calls
const cache = {}; // key -> { data, ts }
const TTL_MS = 60 * 1000; // 1 minute

app.use(express.static(path.join(__dirname, 'public')));

function isFresh(entry) {
  return entry && (Date.now() - entry.ts) < TTL_MS;
}

function parseRepoParam(repo) {
  if (!repo) return null;
  const m = repo.match(/^([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)$/);
  if (!m) return null;
  return `${m[1]}/${m[2]}`;
}

async function ghFetch(url) {
  const res = await fetch(url, {
    headers: {
      'Accept': 'application/vnd.github+json',
      'User-Agent': 'ghcpd-joseph_test_repo-proxy'
    }
  });
  if (res.status === 403) {
    const remaining = res.headers.get('x-ratelimit-remaining');
    const reset = res.headers.get('x-ratelimit-reset');
    const resetDate = reset ? new Date(parseInt(reset, 10) * 1000) : null;
    const msg = `GitHub rate limit exceeded. Remaining=${remaining}. Reset=${resetDate}`;
    const err = new Error(msg);
    err.status = 429;
    throw err;
  }
  if (!res.ok) {
    const text = await res.text();
    const err = new Error(`GitHub API error: ${res.status} ${text}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

app.get('/api/prs', async (req, res) => {
  const repo = parseRepoParam(req.query.repo);
  if (!repo) return res.status(400).json({ error: 'Invalid repo format. Use owner/repo' });
  const key = `prs:${repo}`;
  if (isFresh(cache[key])) return res.json(cache[key].data);
  try {
    const data = await ghFetch(`https://api.github.com/repos/${repo}/pulls?state=all&per_page=30`);
    cache[key] = { data, ts: Date.now() };
    res.json(data);
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
});

app.get('/api/prs/:number', async (req, res) => {
  const repo = parseRepoParam(req.query.repo);
  if (!repo) return res.status(400).json({ error: 'Invalid repo format. Use owner/repo' });
  const number = parseInt(req.params.number, 10);
  if (!number) return res.status(400).json({ error: 'Invalid PR number' });
  const key = `pr:${repo}:${number}`;
  if (isFresh(cache[key])) return res.json(cache[key].data);
  try {
    const data = await ghFetch(`https://api.github.com/repos/${repo}/pulls/${number}`);
    cache[key] = { data, ts: Date.now() };
    res.json(data);
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
});

app.get('/api/issues', async (req, res) => {
  const repo = parseRepoParam(req.query.repo);
  if (!repo) return res.status(400).json({ error: 'Invalid repo format. Use owner/repo' });
  const key = `issues:${repo}`;
  if (isFresh(cache[key])) return res.json(cache[key].data);
  try {
    const all = await ghFetch(`https://api.github.com/repos/${repo}/issues?state=all&per_page=30`);
    const issuesOnly = all.filter(item => !item.pull_request); // exclude PRs
    cache[key] = { data: issuesOnly, ts: Date.now() };
    res.json(issuesOnly);
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
});

app.get('/api/issues/:number', async (req, res) => {
  const repo = parseRepoParam(req.query.repo);
  if (!repo) return res.status(400).json({ error: 'Invalid repo format. Use owner/repo' });
  const number = parseInt(req.params.number, 10);
  if (!number) return res.status(400).json({ error: 'Invalid issue number' });
  const key = `issue:${repo}:${number}`;
  if (isFresh(cache[key])) return res.json(cache[key].data);
  try {
    const data = await ghFetch(`https://api.github.com/repos/${repo}/issues/${number}`);
    cache[key] = { data, ts: Date.now() };
    res.json(data);
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
