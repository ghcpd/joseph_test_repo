const repositoryForm = document.getElementById('repository-form');
const repoInput = document.getElementById('repository-url');
const typeSelect = document.getElementById('data-type');
const itemSelect = document.getElementById('item-select');
const statusMessage = document.getElementById('status-message');
const detailsPanel = document.getElementById('item-details');
const detailTemplate = document.getElementById('detail-template');

const fetchCache = new Map();
let currentRepoIdentifier = null;
let currentDataType = typeSelect.value;
let currentItems = new Map();

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short'
});

repositoryForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const repoUrl = repoInput.value.trim();
  const parsedRepo = parseRepositoryUrl(repoUrl);

  if (!parsedRepo) {
    alert('Please provide a valid GitHub repository URL in the form https://github.com/owner/repository');
    displayStatus('Unable to parse the repository URL. Please check and try again.', 'error');
    return;
  }

  currentRepoIdentifier = `${parsedRepo.owner}/${parsedRepo.repo}`;
  await loadItems(currentRepoIdentifier, currentDataType);
});

typeSelect.addEventListener('change', async (event) => {
  currentDataType = event.target.value;
  if (!currentRepoIdentifier) {
    displayStatus('Enter a repository URL first, then choose what to load.', 'info');
    return;
  }

  await loadItems(currentRepoIdentifier, currentDataType);
});

itemSelect.addEventListener('change', () => {
  const selectedKey = itemSelect.value;
  if (!selectedKey || !currentItems.has(selectedKey)) {
    renderPlaceholder();
    return;
  }

  const item = currentItems.get(selectedKey);
  renderDetails(item, currentDataType);
});

function parseRepositoryUrl(url) {
  try {
    const parsed = new URL(url);
    if (parsed.hostname !== 'github.com') {
      return null;
    }

    const segments = parsed.pathname.split('/').filter(Boolean);
    if (segments.length < 2) {
      return null;
    }

    const [owner, repo] = segments;
    return { owner, repo: repo.replace(/\.git$/, '') };
  } catch (error) {
    return null;
  }
}

async function loadItems(repoIdentifier, type) {
  updateLoadingState(true);
  displayStatus(`Loading ${type === 'pulls' ? 'pull requests' : 'issues'} for ${repoIdentifier}...`, 'info');

  try {
    const items = await fetchRepositoryData(repoIdentifier, type);
    populateItemSelect(items, type);
    renderPlaceholder();

    if (!items.length) {
      displayStatus(`No ${type === 'pulls' ? 'pull requests' : 'issues'} found for ${repoIdentifier}.`, 'info');
      renderPlaceholder('No results to display.');
    } else {
      displayStatus(`Loaded ${items.length} ${type === 'pulls' ? 'pull requests' : 'issues'} for ${repoIdentifier}.`, 'success');
    }
  } catch (error) {
    console.error(error);
    const message = error.userMessage ?? 'Something went wrong while fetching data from GitHub. Please try again later.';
    alert(message);
    displayStatus(message, 'error');
    currentItems.clear();
    renderPlaceholder('Unable to load data.');
  } finally {
    updateLoadingState(false);
  }
}

async function fetchRepositoryData(repoIdentifier, type) {
  const cacheKey = `${repoIdentifier}|${type}`;
  if (fetchCache.has(cacheKey)) {
    return fetchCache.get(cacheKey);
  }

  const endpoint = getEndpoint(repoIdentifier, type);
  const response = await fetch(endpoint, {
    headers: {
      Accept: 'application/vnd.github+json'
    }
  });

  if (!response.ok) {
    const error = new Error(`GitHub API responded with status ${response.status}`);

    if (response.status === 404) {
      error.userMessage = 'Repository not found. Ensure the URL points to a public GitHub repository.';
    } else if (response.status === 403) {
      const rateLimitRemaining = response.headers.get('X-RateLimit-Remaining');
      if (rateLimitRemaining === '0') {
        error.userMessage = 'GitHub rate limit reached. Please wait a minute before trying again.';
      } else {
        error.userMessage = 'Access forbidden. This repository may be private or restricted.';
      }
    }

    throw error;
  }

  const data = await response.json();
  const normalized = Array.isArray(data) ? data : [];
  let items = normalized;

  if (type === 'issues') {
    items = normalized.filter((entry) => !entry.pull_request);
  }

  const trimmed = items.slice(0, 100);
  fetchCache.set(cacheKey, trimmed);
  return trimmed;
}

function getEndpoint(repoIdentifier, type) {
  const base = `https://api.github.com/repos/${repoIdentifier}`;
  if (type === 'pulls') {
    return `${base}/pulls?state=all&per_page=100`;
  }

  return `${base}/issues?state=all&per_page=100`;
}

function populateItemSelect(items, type) {
  itemSelect.innerHTML = '';
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'Select an item';
  itemSelect.appendChild(placeholder);

  currentItems = new Map();

  items.forEach((item) => {
    const option = document.createElement('option');
    option.value = String(item.id);
    option.textContent = formatOptionLabel(item);

    if (Array.isArray(item.labels) && item.labels.some((label) => label.name.toLowerCase() === 'bug')) {
      option.classList.add('bug-badge');
      option.textContent = `🐞 ${option.textContent}`;
    }

    currentItems.set(option.value, item);
    itemSelect.appendChild(option);
  });

  if (items.length === 0) {
    itemSelect.value = '';
  }
}

function formatOptionLabel(item) {
  const number = item.number ? `#${item.number}` : '';
  return number ? `${number}: ${item.title}` : item.title;
}

function displayStatus(message, tone = 'info') {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${tone}`;
}

function updateLoadingState(isLoading) {
  repositoryForm.querySelector('button[type="submit"]').disabled = isLoading;
  typeSelect.disabled = isLoading;
  itemSelect.disabled = isLoading || itemSelect.options.length <= 1;
  detailsPanel.classList.toggle('loading', isLoading);
}

function renderPlaceholder(message = 'Select a pull request or issue to view its details.') {
  detailsPanel.innerHTML = `<p class="placeholder">${message}</p>`;
}

function renderDetails(item, type) {
  const clone = detailTemplate.content.cloneNode(true);
  const titleField = clone.querySelector('[data-field="title"]');
  const authorField = clone.querySelector('[data-field="author"]');
  const statusField = clone.querySelector('[data-field="status"]');
  const createdField = clone.querySelector('[data-field="created"]');
  const updatedField = clone.querySelector('[data-field="updated"]');
  const bodyField = clone.querySelector('[data-field="body"]');

  titleField.textContent = `${item.title}`;
  authorField.textContent = item.user?.login ?? 'Unknown';
  statusField.textContent = formatStatus(item, type);

displayStatus('Enter a repository URL to begin.', 'info');
renderPlaceholder();

  createdField.textContent = formatDate(item.created_at);
  updatedField.textContent = formatDate(item.updated_at);
  bodyField.textContent = item.body?.trim() || 'No description provided.';

  const hasBugLabel = Array.isArray(item.labels) && item.labels.some((label) => label.name.toLowerCase() === 'bug');
  if (hasBugLabel) {
    const badge = document.createElement('span');
    badge.className = 'bug-highlight';
    badge.textContent = 'Bug label present';
    statusField.append(' · ', badge);
  }

  detailsPanel.innerHTML = '';
  detailsPanel.appendChild(clone);
}

function formatStatus(item, type) {
  if (type === 'pulls') {
    if (item.state === 'open') {
      return 'Open';
    }

    return item.merged_at ? 'Merged' : 'Closed';
  }

  return item.state ? item.state.charAt(0).toUpperCase() + item.state.slice(1) : 'Unknown';
}

function formatDate(dateString) {
  if (!dateString) {
    return 'Unknown';
  }

  try {
    return dateFormatter.format(new Date(dateString));
  } catch (error) {
    return dateString;
  }
}
