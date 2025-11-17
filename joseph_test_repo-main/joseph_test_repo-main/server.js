const express = require('express');
const http = require('http');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

const cache = new Map();
const CACHE_TTL_MS = 60 * 1000; // 1 minute cache to avoid hitting rate limits
let serverInstance;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

function normalizeRepo(input) {
  if (!input || typeof input !== 'string') {
    return null;
  }
  const trimmed = input.trim();
  if (!trimmed) {
    return null;
  }

  const urlPattern = /^https?:\/\/github\.com\/([\w.-]+)\/([\w.-]+)(?:\/)?$/i;
  const shortPattern = /^([\w.-]+)\/([\w.-]+)$/;

  let match = trimmed.match(urlPattern);
  if (match) {
    return `${match[1]}/${match[2]}`;
  }

  match = trimmed.match(shortPattern);
  if (match) {
    return `${match[1]}/${match[2]}`;
  }

  return null;
}

function getCacheKey(type, repo) {
  return `${type}:${repo}`;
}

async function fetchFromGitHub(type, repo) {
  const cacheKey = getCacheKey(type, repo);
  const existing = cache.get(cacheKey);
  const now = Date.now();
  if (existing && now - existing.timestamp < CACHE_TTL_MS) {
    return existing.data;
  }

  let endpoint = '';
  if (type === 'prs') {
    endpoint = `https://api.github.com/repos/${repo}/pulls?state=all&per_page=30`;
  } else if (type === 'issues') {
    endpoint = `https://api.github.com/repos/${repo}/issues?state=all&per_page=30`;
  } else {
    throw new Error('Unsupported type');
  }

  const response = await fetch(endpoint, {
    headers: {
      'User-Agent': 'github-proxy-app',
      Accept: 'application/vnd.github+json'
    }
  });

  if (response.status === 403 && response.headers.get('x-ratelimit-remaining') === '0') {
    throw new Error('GitHub API rate limit exceeded. Please try again later.');
  }

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`GitHub API error: ${response.status} ${message}`);
  }

  const data = await response.json();
  cache.set(cacheKey, { data, timestamp: now });
  return data;
}

function filterIssues(data) {
  if (!Array.isArray(data)) {
    return [];
  }
  return data.filter(item => !item.pull_request);
}

app.get('/api/prs', async (req, res) => {
  const repo = normalizeRepo(req.query.repo);
  if (!repo) {
    return res.status(400).json({ error: 'Invalid repository. Provide a GitHub repo URL or owner/repo.' });
  }

  try {
    const data = await fetchFromGitHub('prs', repo);
    res.json({ repo, items: data });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/issues', async (req, res) => {
  const repo = normalizeRepo(req.query.repo);
  if (!repo) {
    return res.status(400).json({ error: 'Invalid repository. Provide a GitHub repo URL or owner/repo.' });
  }

  try {
    const data = await fetchFromGitHub('issues', repo);
    res.json({ repo, items: filterIssues(data) });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/', (_req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

if (require.main === module) {
  serverInstance = http.createServer(app);
  serverInstance.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

module.exports = app;
module.exports.serverInstance = serverInstance;
