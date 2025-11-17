const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const MAX_RESULTS = 20;

app.use(express.static(path.join(__dirname, 'public')));

function validateRepoParam(repo) {
  return typeof repo === 'string' && /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo.trim());
}

async function fetchFromGitHub(url) {
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'interactive-gh-viewer',
      Accept: 'application/vnd.github+json'
    }
  });

  if (!response.ok) {
    const message = response.status === 403
      ? 'GitHub API rate limit reached. Please try again later.'
      : `GitHub API request failed with status ${response.status}.`;
    throw Object.assign(new Error(message), { statusCode: response.status });
  }

  return response.json();
}

function mapPullRequest(pr) {
  return {
    id: pr.id,
    number: pr.number,
    title: pr.title,
    author: pr.user ? pr.user.login : 'Unknown',
    state: pr.merged_at ? 'merged' : pr.state,
    created_at: pr.created_at,
    updated_at: pr.updated_at,
    body: pr.body,
    html_url: pr.html_url,
    labels: Array.isArray(pr.labels) ? pr.labels.map((label) => label.name) : []
  };
}

function mapIssue(issue) {
  return {
    id: issue.id,
    number: issue.number,
    title: issue.title,
    author: issue.user ? issue.user.login : 'Unknown',
    state: issue.state,
    created_at: issue.created_at,
    updated_at: issue.updated_at,
    body: issue.body,
    html_url: issue.html_url,
    labels: Array.isArray(issue.labels) ? issue.labels.map((label) => label.name) : []
  };
}

app.get('/api/prs', async (req, res) => {
  const repo = req.query.repo;

  if (!validateRepoParam(repo)) {
    return res.status(400).json({ error: 'Invalid repo parameter. Provide it as "owner/repo".' });
  }

  const url = `https://api.github.com/repos/${repo}/pulls?state=all&per_page=${MAX_RESULTS}`;

  try {
    const data = await fetchFromGitHub(url);
    res.json(data.map(mapPullRequest));
  } catch (err) {
    res.status(err.statusCode || 500).json({ error: err.message || 'Unknown error occurred.' });
  }
});

app.get('/api/issues', async (req, res) => {
  const repo = req.query.repo;

  if (!validateRepoParam(repo)) {
    return res.status(400).json({ error: 'Invalid repo parameter. Provide it as "owner/repo".' });
  }

  const url = `https://api.github.com/repos/${repo}/issues?state=all&per_page=${MAX_RESULTS}`;

  try {
    const data = await fetchFromGitHub(url);
    const issuesOnly = data.filter((item) => !item.pull_request);
    res.json(issuesOnly.map(mapIssue));
  } catch (err) {
    res.status(err.statusCode || 500).json({ error: err.message || 'Unknown error occurred.' });
  }
});

if (require.main === module) {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

module.exports = {
  app,
  validateRepoParam,
  mapPullRequest,
  mapIssue
};
