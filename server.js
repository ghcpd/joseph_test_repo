const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Serve static files with proper MIME types
app.use(express.static(__dirname, {
  setHeaders: (res, path) => {
    if (path.endsWith('.css')) {
      res.setHeader('Content-Type', 'text/css');
    } else if (path.endsWith('.js')) {
      res.setHeader('Content-Type', 'application/javascript');
    }
  }
}));

// Serve the main HTML file
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// GitHub API proxy route for Pull Requests
app.get('/api/prs', async (req, res) => {
  try {
    const { repo } = req.query;
    
    if (!repo) {
      return res.status(400).json({ error: 'Repository parameter is required' });
    }
    
    // Validate repo format (user/repo)
    if (!repo.match(/^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/)) {
      return res.status(400).json({ error: 'Invalid repository format. Expected: user/repo' });
    }
    
    const response = await axios.get(`https://api.github.com/repos/${repo}/pulls`, {
      headers: {
        'User-Agent': 'GitHub-PR-Issue-Viewer',
        'Accept': 'application/vnd.github.v3+json'
      }
    });
    
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching pull requests:', error.message);
    
    if (error.response) {
      if (error.response.status === 404) {
        res.status(404).json({ error: 'Repository not found' });
      } else if (error.response.status === 403) {
        res.status(403).json({ error: 'Rate limit exceeded or forbidden' });
      } else {
        res.status(error.response.status).json({ error: error.response.data.message || 'GitHub API error' });
      }
    } else {
      res.status(500).json({ error: 'Internal server error' });
    }
  }
});

// GitHub API proxy route for Issues
app.get('/api/issues', async (req, res) => {
  try {
    const { repo } = req.query;
    
    if (!repo) {
      return res.status(400).json({ error: 'Repository parameter is required' });
    }
    
    // Validate repo format (user/repo)
    if (!repo.match(/^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/)) {
      return res.status(400).json({ error: 'Invalid repository format. Expected: user/repo' });
    }
    
    const response = await axios.get(`https://api.github.com/repos/${repo}/issues`, {
      headers: {
        'User-Agent': 'GitHub-PR-Issue-Viewer',
        'Accept': 'application/vnd.github.v3+json'
      }
    });
    
    // Filter out pull requests (GitHub API returns PRs as issues)
    const issues = response.data.filter(item => !item.pull_request);
    
    res.json(issues);
  } catch (error) {
    console.error('Error fetching issues:', error.message);
    
    if (error.response) {
      if (error.response.status === 404) {
        res.status(404).json({ error: 'Repository not found' });
      } else if (error.response.status === 403) {
        res.status(403).json({ error: 'Rate limit exceeded or forbidden' });
      } else {
        res.status(error.response.status).json({ error: error.response.data.message || 'GitHub API error' });
      }
    } else {
      res.status(500).json({ error: 'Internal server error' });
    }
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});