const express = require('express');
const fetch = require('cross-fetch');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const GITHUB_API_URL = 'https://api.github.com';

app.use(express.static(path.join(__dirname, 'public')));

function buildHeaders() {
  const headers = {
    Accept: 'application/vnd.github+json',
    'User-Agent': 'github-interactive-viewer'
  };

  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }

  return headers;
}

function sanitizeRepoParam(rawRepo) {
  if (!rawRepo || typeof rawRepo !== 'string') {
    return null;
  }

  const trimmed = rawRepo.trim();
  const repoPattern = /^([a-zA-Z0-9_.-]+)\/([a-zA-Z0-9_.-]+)$/;
  const match = trimmed.match(repoPattern);

  return match ? `${match[1]}/${match[2]}` : null;
}

async function fetchFromGitHub(endpoint, res) {
  try {
    const response = await fetch(`${GITHUB_API_URL}/${endpoint}`, {
      headers: buildHeaders()
    });

    if (!response.ok) {
      const message = await response.text();
      res
        .status(response.status)
        .json({ error: message || 'Unable to complete GitHub request.' });
      return null;
    }

    return response.json();
  } catch (error) {
    res.status(500).json({ error: 'Unexpected server error', details: error.message });
    return null;
  }
}

app.get('/api/pull-requests', async (req, res) => {
  const repo = sanitizeRepoParam(req.query.repo);

  if (!repo) {
    res.status(400).json({ error: 'Invalid repository parameter. Expected owner/repo.' });
    return;
  }

  const data = await fetchFromGitHub(`repos/${repo}/pulls?state=all`, res);
  if (!data) {
    return;
  }

  res.json(
    data.map((pr) => ({
      number: pr.number,
      title: pr.title,
      user: pr.user?.login || 'unknown',
      state: pr.state,
      merged_at: pr.merged_at
    }))
  );
});

app.get('/api/pull-requests/:number', async (req, res) => {
  const repo = sanitizeRepoParam(req.query.repo);
  const { number } = req.params;

  if (!repo) {
    res.status(400).json({ error: 'Invalid repository parameter. Expected owner/repo.' });
    return;
  }

  const data = await fetchFromGitHub(`repos/${repo}/pulls/${number}`, res);
  if (!data) {
    return;
  }

  res.json({
    title: data.title,
    user: data.user?.login || 'unknown',
    state: data.state,
    merged: Boolean(data.merged_at),
    created_at: data.created_at,
    updated_at: data.updated_at,
    body: data.body || ''
  });
});

app.get('/api/issues', async (req, res) => {
  const repo = sanitizeRepoParam(req.query.repo);

  if (!repo) {
    res.status(400).json({ error: 'Invalid repository parameter. Expected owner/repo.' });
    return;
  }

  const data = await fetchFromGitHub(`repos/${repo}/issues?state=all`, res);
  if (!data) {
    return;
  }

  const issues = data.filter((item) => !item.pull_request);

  res.json(
    issues.map((issue) => ({
      number: issue.number,
      title: issue.title,
      user: issue.user?.login || 'unknown',
      state: issue.state
    }))
  );
});

app.get('/api/issues/:number', async (req, res) => {
  const repo = sanitizeRepoParam(req.query.repo);
  const { number } = req.params;

  if (!repo) {
    res.status(400).json({ error: 'Invalid repository parameter. Expected owner/repo.' });
    return;
  }

  const data = await fetchFromGitHub(`repos/${repo}/issues/${number}`, res);
  if (!data) {
    return;
  }

  res.json({
    title: data.title,
    user: data.user?.login || 'unknown',
    state: data.state,
    labels: data.labels?.map((label) => label.name) || [],
    created_at: data.created_at,
    updated_at: data.updated_at,
    body: data.body || ''
  });
});

app.get('*', (_, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});