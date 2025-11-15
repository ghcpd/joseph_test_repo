const GITHUB_BASE_URL = 'https://api.github.com';
const API_PROXY_PATH = '/api/github';

export function parseRepositoryUrl(input) {
  if (!input || typeof input !== 'string') {
    throw new Error('Repository URL cannot be empty.');
  }

  const trimmed = input.trim();
  const match = trimmed.match(/^https?:\/\/github\.com\/([^\/\s]+)\/([^\s\/]+?)(?:\.git)?\/?$/i);

  if (!match) {
    throw new Error('Please enter a valid GitHub repository URL like https://github.com/user/repo.');
  }

  const [, owner, repo] = match;
  return { owner, repo };
}

export function buildApiUrl(owner, repo, dataType) {
  const encodedOwner = encodeURIComponent(owner);
  const encodedRepo = encodeURIComponent(repo);
  const base = `${GITHUB_BASE_URL}/repos/${encodedOwner}/${encodedRepo}`;

  if (dataType === 'pulls') {
    return `${base}/pulls?state=all&per_page=50&sort=updated&direction=desc`;
  }

  return `${base}/issues?state=all&per_page=50&sort=updated&direction=desc`;
}

export async function fetchRepositoryItems(owner, repo, dataType) {
  const params = new URLSearchParams({ owner, repo, type: dataType });
  const proxyUrl = `${API_PROXY_PATH}?${params.toString()}`;

  let response;

  try {
    response = await fetch(proxyUrl, {
      headers: {
        Accept: 'application/json'
      }
    });
  } catch (error) {
    console.warn('Proxy request failed, attempting direct GitHub fetch.', error);
  }

  if (!response || !response.ok) {
    try {
      response = await fetch(buildApiUrl(owner, repo, dataType), {
        headers: {
          Accept: 'application/vnd.github+json'
        }
      });
    } catch (networkError) {
      console.error('GitHub fetch failed:', networkError);
      throw new Error('Failed to fetch data from GitHub.');
    }
  }

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Repository not found or is private.');
    }

    if (response.status === 403) {
      throw new Error('API rate limit exceeded. Please try again later.');
    }

    const text = await response.text();
    throw new Error(`GitHub API error: ${response.status} ${response.statusText}: ${text}`);
  }

  const rawItems = await response.json();

  if (!Array.isArray(rawItems) || rawItems.length === 0) {
    return [];
  }

  return rawItems
    .map((item) => normaliseItem(item, dataType))
    .filter(Boolean);
}

export function normaliseItem(item, dataType) {
  if (!item) {
    return null;
  }

  if (dataType === 'issues' && item.pull_request) {
    return null;
  }

  const labels = Array.isArray(item.labels)
    ? item.labels.map((label) => label && label.name).filter(Boolean)
    : [];

  return {
    id: item.id,
    number: item.number,
    title: item.title || '(No title)',
    user: item.user ? item.user.login : 'unknown',
    state:
      dataType === 'pulls'
        ? item.merged_at
          ? 'merged'
          : item.state
        : item.state,
    created_at: item.created_at,
    updated_at: item.updated_at,
    body: item.body || 'No description provided.',
    html_url: item.html_url,
    labels,
    isBug: labels.some((label) => label.toLowerCase() === 'bug'),
    dataType
  };
}

export function createSummary(items) {
  if (!Array.isArray(items) || items.length === 0) {
    return { count: 0, authors: [], states: {}, bugCount: 0 };
  }

  const authors = new Set();
  const states = {};
  let bugCount = 0;

  for (const item of items) {
    if (item.user) {
      authors.add(item.user);
    }

    const status = item.state || 'unknown';
    states[status] = (states[status] || 0) + 1;

    if (item.isBug) {
      bugCount += 1;
    }
  }

  return {
    count: items.length,
    authors: Array.from(authors),
    states,
    bugCount
  };
}
