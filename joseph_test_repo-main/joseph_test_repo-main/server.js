const express = require('express');
const path = require('path');
const fetch = require('node-fetch');

const PORT = process.env.PORT || 3000;
const GITHUB_API_BASE = 'https://api.github.com';
const CACHE_DURATION_MS = 60 * 1000; // 1 minute cache to limit GitHub API calls
const repoPattern = /^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/;

const app = express();
const cache = new Map();

app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

function validateRepo(repo) {
  if (!repo || !repoPattern.test(repo)) {
    const error = new Error('Invalid repository. Use the form "owner/repo".');
    error.status = 400;
    throw error;
  }
  return repo.trim();
}

function buildHeaders() {
  const headers = {
    'Accept': 'application/vnd.github+json',
    'User-Agent': 'gh-proxy-interactive'
  };
  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }
  return headers;
}

function getCache(key) {
  const entry = cache.get(key);
  if (!entry) return null;
  const isExpired = Date.now() - entry.timestamp > CACHE_DURATION_MS;
  if (isExpired) {
    cache.delete(key);
    return null;
  }
  return entry.value;
}

function setCache(key, value) {
  cache.set(key, { value, timestamp: Date.now() });
}

async function fetchFromGitHub(endpoint, cacheKey) {
  const cached = getCache(cacheKey);
  if (cached) {
    return cached;
  }

  const response = await fetch(`${GITHUB_API_BASE}${endpoint}`, {
    headers: buildHeaders()
  });

  const rateRemaining = response.headers.get('x-ratelimit-remaining');
  const rateReset = response.headers.get('x-ratelimit-reset');

  if (!response.ok) {
    let errorText = await response.text();
    try {
      const parsed = JSON.parse(errorText);
      errorText = parsed.message || errorText;
    } catch (e) {
      // ignore JSON parse errors
    }

    if (response.status === 403 && rateRemaining === '0') {
      const minutes = rateReset ? Math.ceil((Number(rateReset) * 1000 - Date.now()) / (60 * 1000)) : 'a few';
      const err = new Error(`GitHub API rate limit exceeded. Try again in ${minutes} minute(s).`);
      err.status = 429;
      throw err;
    }

    const err = new Error(errorText || 'GitHub API request failed');
    err.status = response.status;
    throw err;
  }

  const data = await response.json();
  setCache(cacheKey, data);
  return data;
}

function normalizeList(items = [], type = 'pulls') {
  return items.map((item) => ({
    number: item.number,
    title: item.title,
    state: item.state,
    author: item.user ? item.user.login : 'Unknown',
    created_at: item.created_at,
    updated_at: item.updated_at,
    labels: Array.isArray(item.labels) ? item.labels.map((label) => label.name) : [],
    type,
    isIssue: type === 'issues'
  }));
}

function normalizeDetail(item, type) {
  if (!item) return null;
  const common = {
    number: item.number,
    title: item.title,
    state: item.state,
    author: item.user ? item.user.login : 'Unknown',
    created_at: item.created_at,
    updated_at: item.updated_at,
    body: item.body || '',
    labels: Array.isArray(item.labels) ? item.labels.map((label) => label.name) : []
  };

  if (type === 'pulls') {
    return {
      ...common,
      merged: Boolean(item.merged_at),
      type: 'pull_request',
      additions: item.additions,
      deletions: item.deletions,
      changed_files: item.changed_files
    };
  }

  return {
    ...common,
    type: 'issue',
    locked: item.locked,
    comments: item.comments,
    milestone: item.milestone ? item.milestone.title : null
  };
}

app.get('/api/prs', async (req, res, next) => {
  try {
    const repo = validateRepo(req.query.repo);
    const cacheKey = `pulls:list:${repo}`;
    const data = await fetchFromGitHub(`/repos/${repo}/pulls?state=all&per_page=50`, cacheKey);
    res.json(normalizeList(data, 'pulls'));
  } catch (err) {
    next(err);
  }
});

app.get('/api/prs/:number', async (req, res, next) => {
  try {
    const repo = validateRepo(req.query.repo);
    const number = Number(req.params.number);
    if (!Number.isInteger(number)) {
      const error = new Error('Pull request number must be an integer.');
      error.status = 400;
      throw error;
    }
    const cacheKey = `pulls:detail:${repo}:${number}`;
    const data = await fetchFromGitHub(`/repos/${repo}/pulls/${number}`, cacheKey);
    res.json(normalizeDetail(data, 'pulls'));
  } catch (err) {
    next(err);
  }
});

app.get('/api/issues', async (req, res, next) => {
  try {
    const repo = validateRepo(req.query.repo);
    const cacheKey = `issues:list:${repo}`;
    const data = await fetchFromGitHub(`/repos/${repo}/issues?state=all&per_page=50`, cacheKey);
    const filtered = data.filter((item) => !item.pull_request);
    res.json(normalizeList(filtered, 'issues'));
  } catch (err) {
    next(err);
  }
});

app.get('/api/issues/:number', async (req, res, next) => {
  try {
    const repo = validateRepo(req.query.repo);
    const number = Number(req.params.number);
    if (!Number.isInteger(number)) {
      const error = new Error('Issue number must be an integer.');
      error.status = 400;
      throw error;
    }
    const cacheKey = `issues:detail:${repo}:${number}`;
    const data = await fetchFromGitHub(`/repos/${repo}/issues/${number}`, cacheKey);
    res.json(normalizeDetail(data, 'issues'));
  } catch (err) {
    next(err);
  }
});

app.use((err, req, res, next) => {
  const status = err.status || 500;
  res.status(status).json({ error: err.message || 'Internal Server Error' });
});

if (require.main === module) {
  const serverInstance = app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
  });

  const keepAlive = setInterval(() => {}, 1 << 30);

  const shutdown = () => {
    clearInterval(keepAlive);
    serverInstance.close(() => process.exit(0));
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

module.exports = app;
