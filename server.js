const path = require('path');
const express = require('express');

const app = express();
const PORT = process.env.PORT || 3000;
const GITHUB_API_BASE = 'https://api.github.com';

const repoPattern = /^[\w.-]+\/[\w.-]+$/;

app.use(express.static(path.join(__dirname, 'public')));

class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function parseRepoInput(input) {
  if (!input || typeof input !== 'string') {
    return null;
  }

  const trimmed = input.trim();

  if (repoPattern.test(trimmed)) {
    return trimmed;
  }

  try {
    const url = new URL(trimmed);
    if (url.hostname !== 'github.com') {
      return null;
    }

    const segments = url.pathname.split('/').filter(Boolean);
    if (segments.length < 2) {
      return null;
    }

    return `${segments[0]}/${segments[1]}`;
  } catch (error) {
    return null;
  }
}

function buildHeaders() {
  const headers = {
    'User-Agent': 'ghcpd-joseph-test-repo',
    Accept: 'application/vnd.github+json',
  };

  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }

  return headers;
}

function buildRepoPath(repo) {
  return repo
    .split('/')
    .map((segment) => encodeURIComponent(segment))
    .join('/');
}

async function requestGithub(pathname) {
  const response = await fetch(`${GITHUB_API_BASE}${pathname}`, {
    headers: buildHeaders(),
  });

  if (!response.ok) {
    let message = 'GitHub API error';
    try {
      const body = await response.json();
      if (body && body.message) {
        message = body.message;
      }
    } catch (error) {
      // Ignore JSON parsing errors.
    }

    throw new HttpError(response.status, message);
  }

  return response.json();
}

function formatPullRequest(pr) {
  return {
    number: pr.number,
    title: pr.title,
    author: pr.user?.login || 'Unknown',
    state: pr.state,
    merged: Boolean(pr.merged_at),
    created_at: pr.created_at,
    updated_at: pr.updated_at,
    labels: Array.isArray(pr.labels) ? pr.labels.map((label) => label.name) : [],
    body: pr.body || '',
  };
}

function formatIssue(issue) {
  return {
    number: issue.number,
    title: issue.title,
    author: issue.user?.login || 'Unknown',
    state: issue.state,
    created_at: issue.created_at,
    updated_at: issue.updated_at,
    labels: Array.isArray(issue.labels) ? issue.labels.map((label) => label.name) : [],
    body: issue.body || '',
  };
}

function handleError(res, error) {
  if (error instanceof HttpError) {
    res.status(error.status).json({ error: error.message });
    return;
  }

  // eslint-disable-next-line no-console
  console.error(error);
  res.status(500).json({ error: 'Internal server error' });
}

app.get('/api/prs', async (req, res) => {
  const repo = parseRepoInput(req.query.repo);
  if (!repo) {
    res.status(400).json({ error: 'Invalid repository. Provide owner/repo or https://github.com/owner/repo.' });
    return;
  }

  const number = req.query.number;

  try {
    if (number) {
      const data = await requestGithub(`/repos/${buildRepoPath(repo)}/pulls/${encodeURIComponent(number)}`);
      res.json({ item: formatPullRequest(data) });
      return;
    }

    const perPage = Math.min(Math.max(Number(req.query.per_page) || 20, 1), 50);
    const data = await requestGithub(`/repos/${buildRepoPath(repo)}/pulls?state=all&per_page=${perPage}`);
    res.json({ items: data.map(formatPullRequest) });
  } catch (error) {
    handleError(res, error);
  }
});

app.get('/api/issues', async (req, res) => {
  const repo = parseRepoInput(req.query.repo);
  if (!repo) {
    res.status(400).json({ error: 'Invalid repository. Provide owner/repo or https://github.com/owner/repo.' });
    return;
  }

  const number = req.query.number;

  try {
    if (number) {
      const data = await requestGithub(`/repos/${buildRepoPath(repo)}/issues/${encodeURIComponent(number)}`);
      res.json({ item: formatIssue(data) });
      return;
    }

    const perPage = Math.min(Math.max(Number(req.query.per_page) || 20, 1), 50);
    const data = await requestGithub(`/repos/${buildRepoPath(repo)}/issues?state=all&per_page=${perPage}`);
    res.json({ items: data.filter((issue) => !issue.pull_request).map(formatIssue) });
  } catch (error) {
    handleError(res, error);
  }
});

app.use((req, res, next) => {
  if (req.method === 'GET' && !req.path.startsWith('/api/')) {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
    return;
  }
  next();
});

let serverInstance;

async function start() {
  try {
    serverInstance = await app.listen(PORT);
    // eslint-disable-next-line no-console
    console.log(`Server running on http://localhost:${PORT}`);
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Failed to start server', error);
    process.exit(1);
  }
}

if (require.main === module) {
  start();
}

function getServerInstance() {
  return serverInstance;
}

module.exports = {
  app,
  parseRepoInput,
  start,
  getServerInstance,
  formatPullRequest,
  formatIssue,
  HttpError,
};