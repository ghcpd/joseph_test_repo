const express = require('express');
const fetch = require('node-fetch');
const path = require('path');

const app = express();
const PORT = 3000;

// Serve static files from public directory
app.use(express.static('public'));

// Helper function to validate GitHub repo format
function parseRepoUrl(repo) {
  // Support both "user/repo" and full URL formats
  const match = repo.match(/(?:https?:\/\/)?(?:www\.)?github\.com\/([^\/]+\/[^\/]+)/);
  if (match) {
    return match[1].replace(/\.git$/, '');
  }
  // Check if it's already in user/repo format
  if (/^[^\/]+\/[^\/]+$/.test(repo)) {
    return repo;
  }
  return null;
}

// Fetch Pull Requests
app.get('/api/prs', async (req, res) => {
  const repo = req.query.repo;
  
  if (!repo) {
    return res.status(400).json({ error: 'Repository parameter is required' });
  }

  const parsedRepo = parseRepoUrl(repo);
  if (!parsedRepo) {
    return res.status(400).json({ error: 'Invalid GitHub repository format' });
  }

  try {
    const apiUrl = `https://api.github.com/repos/${parsedRepo}/pulls?state=all&per_page=100`;
    const response = await fetch(apiUrl, {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'GitHub-PR-Issue-Viewer'
      }
    });

    if (!response.ok) {
      if (response.status === 404) {
        return res.status(404).json({ error: 'Repository not found' });
      }
      if (response.status === 403) {
        const rateLimitReset = response.headers.get('X-RateLimit-Reset');
        return res.status(403).json({ 
          error: 'GitHub API rate limit exceeded',
          resetTime: rateLimitReset ? new Date(rateLimitReset * 1000).toISOString() : null
        });
      }
      return res.status(response.status).json({ error: `GitHub API error: ${response.statusText}` });
    }

    const data = await response.json();
    
    // Transform data to include merged status
    const prs = data.map(pr => ({
      number: pr.number,
      title: pr.title,
      state: pr.state,
      merged: pr.merged_at ? true : false,
      author: pr.user.login,
      created_at: pr.created_at,
      updated_at: pr.updated_at,
      body: pr.body || 'No description provided',
      html_url: pr.html_url,
      labels: pr.labels.map(label => label.name)
    }));

    res.json(prs);
  } catch (error) {
    console.error('Error fetching PRs:', error);
    res.status(500).json({ error: 'Failed to fetch pull requests' });
  }
});

// Fetch Issues
app.get('/api/issues', async (req, res) => {
  const repo = req.query.repo;
  
  if (!repo) {
    return res.status(400).json({ error: 'Repository parameter is required' });
  }

  const parsedRepo = parseRepoUrl(repo);
  if (!parsedRepo) {
    return res.status(400).json({ error: 'Invalid GitHub repository format' });
  }

  try {
    const apiUrl = `https://api.github.com/repos/${parsedRepo}/issues?state=all&per_page=100`;
    const response = await fetch(apiUrl, {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'GitHub-PR-Issue-Viewer'
      }
    });

    if (!response.ok) {
      if (response.status === 404) {
        return res.status(404).json({ error: 'Repository not found' });
      }
      if (response.status === 403) {
        const rateLimitReset = response.headers.get('X-RateLimit-Reset');
        return res.status(403).json({ 
          error: 'GitHub API rate limit exceeded',
          resetTime: rateLimitReset ? new Date(rateLimitReset * 1000).toISOString() : null
        });
      }
      return res.status(response.status).json({ error: `GitHub API error: ${response.statusText}` });
    }

    const data = await response.json();
    
    // Filter out pull requests (issues that have a pull_request field)
    const issues = data
      .filter(item => !item.pull_request)
      .map(issue => ({
        number: issue.number,
        title: issue.title,
        state: issue.state,
        author: issue.user.login,
        created_at: issue.created_at,
        updated_at: issue.updated_at,
        body: issue.body || 'No description provided',
        html_url: issue.html_url,
        labels: issue.labels.map(label => label.name)
      }));

    res.json(issues);
  } catch (error) {
    console.error('Error fetching issues:', error);
    res.status(500).json({ error: 'Failed to fetch issues' });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log('Press Ctrl+C to stop the server');
});
