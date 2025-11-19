const express = require('express');
const path = require('path');
const http = require('http');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, 'public')));

const GITHUB_API_BASE = 'https://api.github.com/repos/';
const USER_AGENT = 'interactive-pr-issue-viewer';

function normalizeRepoInput(repoInput) {
  if (!repoInput || typeof repoInput !== 'string') {
    throw new Error('Repository parameter is required');
  }

  const trimmed = repoInput.trim();
  if (trimmed.startsWith('https://github.com/')) {
    const parts = trimmed.replace('https://github.com/', '').split('/');
    if (parts.length >= 2) {
      return `${parts[0]}/${parts[1]}`;
    }
  }

  if (/^[^\s\/]+\/[^\s\/]+$/.test(trimmed)) {
    return trimmed;
  }

  throw new Error('Repository parameter must be in the form owner/repo or https://github.com/owner/repo');
}

async function fetchFromGitHub(endpoint) {
  const headers = {
    'Accept': 'application/vnd.github+json',
    'User-Agent': USER_AGENT,
  };

  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }

  const response = await fetch(endpoint, { headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ message: response.statusText }));
    const error = new Error(body.message || 'Failed to fetch from GitHub');
    error.status = response.status;
    throw error;
  }

  return response.json();
}

app.get('/api/prs', async (req, res) => {
  try {
    const repo = normalizeRepoInput(req.query.repo);
    const url = `${GITHUB_API_BASE}${repo}/pulls?state=all&per_page=50`;
    const pulls = await fetchFromGitHub(url);
    const simplified = pulls.map((pr) => ({
      number: pr.number,
      title: pr.title,
    }));
    res.json({ items: simplified });
  } catch (error) {
    const status = error.status || 500;
    res.status(status).json({ error: error.message || 'Unexpected server error' });
  }
});

app.get('/api/issues', async (req, res) => {
  try {
    const repo = normalizeRepoInput(req.query.repo);
    const url = `${GITHUB_API_BASE}${repo}/issues?state=all&per_page=50`;
    const issues = await fetchFromGitHub(url);
    const filtered = issues.filter((issue) => !issue.pull_request);
    const simplified = filtered.map((issue) => ({
      number: issue.number,
      title: issue.title,
    }));
    res.json({ items: simplified });
  } catch (error) {
    const status = error.status || 500;
    res.status(status).json({ error: error.message || 'Unexpected server error' });
  }
});

app.get('/api/prs/:number', async (req, res) => {
  try {
    const repo = normalizeRepoInput(req.query.repo);
    const number = parseInt(req.params.number, 10);
    if (Number.isNaN(number)) {
      return res.status(400).json({ error: 'Pull request number must be numeric' });
    }
    const url = `${GITHUB_API_BASE}${repo}/pulls/${number}`;
    const pr = await fetchFromGitHub(url);
    res.json({
      title: pr.title,
      author: pr.user ? pr.user.login : 'Unknown',
      status: pr.merged_at ? 'merged' : pr.state,
      created_at: pr.created_at,
      updated_at: pr.updated_at,
      body: pr.body || '',
      html_url: pr.html_url,
      labels: (pr.labels || []).map((label) => label.name),
    });
  } catch (error) {
    const status = error.status || 500;
    res.status(status).json({ error: error.message || 'Unexpected server error' });
  }
});

app.get('/api/issues/:number', async (req, res) => {
  try {
    const repo = normalizeRepoInput(req.query.repo);
    const number = parseInt(req.params.number, 10);
    if (Number.isNaN(number)) {
      return res.status(400).json({ error: 'Issue number must be numeric' });
    }
    const url = `${GITHUB_API_BASE}${repo}/issues/${number}`;
    const issue = await fetchFromGitHub(url);
    res.json({
      title: issue.title,
      author: issue.user ? issue.user.login : 'Unknown',
      status: issue.state,
      created_at: issue.created_at,
      updated_at: issue.updated_at,
      body: issue.body || '',
      html_url: issue.html_url,
      labels: (issue.labels || []).map((label) => label.name),
    });
  } catch (error) {
    const status = error.status || 500;
    res.status(status).json({ error: error.message || 'Unexpected server error' });
  }
});

app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

const server = http.createServer(app);

server.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});