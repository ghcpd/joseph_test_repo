const path = require('path');
const express = require('express');
const fetch = require('node-fetch');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const repoRegex = /^[\w.-]+\/[\w.-]+$/;
const cache = new Map();
const CACHE_DURATION_MS = 60 * 1000;

function normalizeRepo(repoInput) {
  if (!repoInput) {
    return null;
  }

  const trimmed = repoInput.trim();

  if (repoRegex.test(trimmed)) {
    return trimmed;
  }

  const match = trimmed.match(/^https?:\/\/github\.com\/([^\s/]+\/[^\s/?#]+)/i);
  if (!match) {
    return null;
  }

  const repoPart = match[1].replace(/\.git$/, '');
  return repoRegex.test(repoPart) ? repoPart : null;
}

function getCacheKey(type, repo, id) {
  return [type, repo, id || 'list'].join(':');
}

function setCache(key, value) {
  cache.set(key, { value, timestamp: Date.now() });
}

function getCache(key) {
  const cached = cache.get(key);
  if (!cached) {
    return null;
  }
  if (Date.now() - cached.timestamp > CACHE_DURATION_MS) {
    cache.delete(key);
    return null;
  }
  return cached.value;
}

async function githubRequest(url) {
  const headers = {
    'User-Agent': 'gh-proxy-app',
    Accept: 'application/vnd.github+json'
  };

  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }

  const response = await fetch(url, { headers });
  if (response.status === 403 && response.headers.get('x-ratelimit-remaining') === '0') {
    const reset = response.headers.get('x-ratelimit-reset');
    const resetSeconds = reset ? Math.max(0, parseInt(reset, 10) * 1000 - Date.now()) : null;
    const resetMinutes = resetSeconds ? Math.ceil(resetSeconds / 60000) : null;
    const message = resetMinutes
      ? `GitHub rate limit exceeded. Try again in ~${resetMinutes} minute(s).`
      : 'GitHub rate limit exceeded. Please try again later.';
    const error = new Error(message);
    error.status = 429;
    throw error;
  }

  if (!response.ok) {
    const errorBody = await response.text();
    const error = new Error(`GitHub API error: ${response.status} ${errorBody}`);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

async function fetchList({ type, repo }) {
  const cacheKey = getCacheKey(type, repo);
  const cached = getCache(cacheKey);
  if (cached) {
    return cached;
  }

  const resource = type === 'prs' ? 'pulls' : 'issues';
  const url = `https://api.github.com/repos/${repo}/${resource}?state=all&per_page=50`;
  const data = await githubRequest(url);
  setCache(cacheKey, data);
  return data;
}

async function fetchDetails({ type, repo, number }) {
  const cacheKey = getCacheKey(type, repo, number);
  const cached = getCache(cacheKey);
  if (cached) {
    return cached;
  }

  const resource = type === 'prs' ? 'pulls' : 'issues';
  const url = `https://api.github.com/repos/${repo}/${resource}/${number}`;
  const data = await githubRequest(url);
  setCache(cacheKey, data);
  return data;
}

function sendError(res, status, message) {
  res.status(status).json({ error: message });
}

app.get('/api/prs', async (req, res) => {
  const repo = normalizeRepo(req.query.repo);
  if (!repo) {
    return sendError(res, 400, 'Invalid repository format. Use owner/repo or full GitHub URL.');
  }

  try {
    const data = await fetchList({ type: 'prs', repo });
    res.json(data);
  } catch (error) {
    sendError(res, error.status || 500, error.message);
  }
});

app.get('/api/issues', async (req, res) => {
  const repo = normalizeRepo(req.query.repo);
  if (!repo) {
    return sendError(res, 400, 'Invalid repository format. Use owner/repo or full GitHub URL.');
  }

  try {
    const data = await fetchList({ type: 'issues', repo });
    res.json(data);
  } catch (error) {
    sendError(res, error.status || 500, error.message);
  }
});

app.get('/api/prs/:number', async (req, res) => {
  const repo = normalizeRepo(req.query.repo);
  if (!repo) {
    return sendError(res, 400, 'Invalid repository format. Use owner/repo or full GitHub URL.');
  }

  const number = parseInt(req.params.number, 10);
  if (Number.isNaN(number)) {
    return sendError(res, 400, 'Invalid pull request number.');
  }

  try {
    const data = await fetchDetails({ type: 'prs', repo, number });
    res.json(data);
  } catch (error) {
    sendError(res, error.status || 500, error.message);
  }
});

app.get('/api/issues/:number', async (req, res) => {
  const repo = normalizeRepo(req.query.repo);
  if (!repo) {
    return sendError(res, 400, 'Invalid repository format. Use owner/repo or full GitHub URL.');
  }

  const number = parseInt(req.params.number, 10);
  if (Number.isNaN(number)) {
    return sendError(res, 400, 'Invalid issue number.');
  }

  try {
    const data = await fetchDetails({ type: 'issues', repo, number });
    res.json(data);
  } catch (error) {
    sendError(res, error.status || 500, error.message);
  }
});

module.exports = {
  app,
  normalizeRepo,
  fetchList,
  fetchDetails
};
