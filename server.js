const express = require('express');
const path = require('path');

let fetchModulePromise = null;

async function getFetch() {
  if (!fetchModulePromise) {
    fetchModulePromise = import('node-fetch').then(({ default: fetchImpl }) => fetchImpl);
  }
  return fetchModulePromise;
}

const app = express();
const PORT = process.env.PORT || 3000;
const USER_AGENT = 'github-pr-issue-viewer-demo';
app.use(express.static(path.join(__dirname, 'public')));

function validateRepo(repo) {
  if (typeof repo !== 'string') {
    return false;
  }
  return /^[\w.-]+\/[\w.-]+$/.test(repo.trim());
}

async function fetchFromGitHub(url) {
  const fetchImpl = await getFetch();
  const response = await fetchImpl(url, {
    headers: {
      'User-Agent': USER_AGENT,
      Accept: 'application/vnd.github+json'
    }
  });

  if (!response.ok) {
    const errorBody = await safeJson(response);
    const message = errorBody?.message || `GitHub request failed with status ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

async function safeJson(response) {
  try {
    return await response.json();
  } catch (error) {
    return null;
  }
}

app.get('/api/prs', async (req, res) => {
  const { repo } = req.query;
  if (!validateRepo(repo)) {
    return res.status(400).json({ message: 'Query parameter "repo" must be in the form <owner>/<repository>.' });
  }

  try {
    const data = await fetchFromGitHub(`https://api.github.com/repos/${repo}/pulls?state=all&per_page=30`);
    res.json(data);
  } catch (error) {
    res.status(error.status || 502).json({ message: error.message });
  }
});

app.get('/api/issues', async (req, res) => {
  const { repo } = req.query;
  if (!validateRepo(repo)) {
    return res.status(400).json({ message: 'Query parameter "repo" must be in the form <owner>/<repository>.' });
  }

  try {
    const data = await fetchFromGitHub(`https://api.github.com/repos/${repo}/issues?state=all&per_page=30`);
    const filtered = Array.isArray(data) ? data.filter((item) => !item.pull_request) : [];
    res.json(filtered);
  } catch (error) {
    res.status(error.status || 502).json({ message: error.message });
  }
});

app.get('/api/prs/:number', async (req, res) => {
  const { repo } = req.query;
  const { number } = req.params;
  if (!validateRepo(repo)) {
    return res.status(400).json({ message: 'Query parameter "repo" must be in the form <owner>/<repository>.' });
  }

  try {
    const data = await fetchFromGitHub(`https://api.github.com/repos/${repo}/pulls/${number}`);
    res.json(data);
  } catch (error) {
    res.status(error.status || 502).json({ message: error.message });
  }
});

app.get('/api/issues/:number', async (req, res) => {
  const { repo } = req.query;
  const { number } = req.params;
  if (!validateRepo(repo)) {
    return res.status(400).json({ message: 'Query parameter "repo" must be in the form <owner>/<repository>.' });
  }

  try {
    const data = await fetchFromGitHub(`https://api.github.com/repos/${repo}/issues/${number}`);
    if (data.pull_request) {
      return res.status(404).json({ message: 'Issue not found.' });
    }
    res.json(data);
  } catch (error) {
    res.status(error.status || 502).json({ message: error.message });
  }
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
  });
}

module.exports = app;
