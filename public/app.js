const form = document.getElementById('lookup-form');
const repoInput = document.getElementById('repo-input');
const typeSelect = document.getElementById('type-select');
const itemSelect = document.getElementById('item-select');
const detailsPanel = document.getElementById('details');
const detailsTitle = document.getElementById('details-title');
const detailsAuthor = document.getElementById('details-author');
const detailsStatus = document.getElementById('details-status');
const detailsCreated = document.getElementById('details-created');
const detailsUpdated = document.getElementById('details-updated');
const detailsBody = document.getElementById('details-body');

let activeRepo = '';
const cache = {
  prs: null,
  issues: null
};

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const rawRepo = repoInput.value.trim();
  const normalizedRepo = normalizeRepo(rawRepo);

  if (!normalizedRepo) {
    alert('Please provide a valid GitHub repository URL in the form https://github.com/<owner>/<repo>.');
    return;
  }

  if (normalizedRepo !== activeRepo) {
    cache.prs = null;
    cache.issues = null;
    activeRepo = normalizedRepo;
  }

  await loadItems(typeSelect.value);
});

typeSelect.addEventListener('change', async () => {
  if (!activeRepo) {
    return;
  }
  if (!cache[typeSelect.value]) {
    await loadItems(typeSelect.value);
  } else {
    populateItemSelect(cache[typeSelect.value]);
  }
});

itemSelect.addEventListener('change', async () => {
  const value = itemSelect.value;
  if (!value) {
    showDetails(null);
    return;
  }

  await loadDetails(typeSelect.value, value);
});

function normalizeRepo(value) {
  if (!value) return null;
  const trimmed = value.trim();

  const fullUrlMatch = trimmed.match(/^https:\/\/github\.com\/([\w.-]+)\/([\w.-]+)(?:\/)?$/i);
  if (fullUrlMatch) {
    return `${fullUrlMatch[1]}/${fullUrlMatch[2]}`;
  }

  const shorthandMatch = trimmed.match(/^([\w.-]+)\/([\w.-]+)$/);
  if (shorthandMatch) {
    return trimmed;
  }
  return null;
}

async function loadItems(type) {
  toggleSelect(true, 'Loading…');
  showDetails(null);
  try {
    const response = await fetch(`/api/${type}?repo=${encodeURIComponent(activeRepo)}`);
    if (!response.ok) {
      const message = await extractError(response);
      throw new Error(message || 'Failed to fetch items from GitHub.');
    }
    const items = await response.json();
    cache[type] = items;
    populateItemSelect(items);
  } catch (error) {
    alert(error.message);
    populateItemSelect([]);
  }
}

async function loadDetails(type, number) {
  try {
    const response = await fetch(`/api/${type}/${number}?repo=${encodeURIComponent(activeRepo)}`);
    if (!response.ok) {
      const message = await extractError(response);
      throw new Error(message || 'Failed to load entry details.');
    }

    const details = await response.json();
    showDetails(details);
  } catch (error) {
    alert(error.message);
  }
}

function populateItemSelect(items) {
  itemSelect.innerHTML = '';

  if (!items || !items.length) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'No entries found.';
    itemSelect.append(option);
    itemSelect.disabled = true;
    return;
  }

  const defaultOption = document.createElement('option');
  defaultOption.value = '';
  defaultOption.textContent = `Select a ${typeSelect.value === 'prs' ? 'pull request' : 'issue'}`;
  itemSelect.append(defaultOption);

  for (const item of items) {
    const option = document.createElement('option');
    option.value = item.number;
    option.textContent = formatListing(item);
    if (item.labels && item.labels.some((label) => label.name.toLowerCase() === 'bug')) {
      option.classList.add('bug-option');
    }
    itemSelect.append(option);
  }

  itemSelect.disabled = false;
}

function formatListing(item) {
  const prefix = `#${item.number}`;
  const title = item.title || '(untitled)';
  const labelIndicator = item.labels && item.labels.some((label) => label.name.toLowerCase() === 'bug') ? ' • bug' : '';
  return `${prefix} ${title}${labelIndicator}`;
}

function showDetails(details) {
  if (!details) {
    detailsPanel.classList.add('hidden');
    return;
  }

  detailsPanel.classList.remove('hidden');
  detailsTitle.textContent = details.title || 'Untitled';
  detailsAuthor.textContent = details.user?.login || 'Unknown';
  detailsStatus.textContent = formatStatus(details);
  detailsCreated.textContent = formatDate(details.created_at);
  detailsUpdated.textContent = formatDate(details.updated_at);
  detailsBody.textContent = details.body || 'No description provided.';
}

function formatStatus(details) {
  if (details.merged_at) {
    return 'Merged';
  }
  const state = details.state || 'unknown';
  return state.charAt(0).toUpperCase() + state.slice(1);
}

function formatDate(value) {
  if (!value) {
    return 'Unknown';
  }
  try {
    return new Date(value).toLocaleString();
  } catch (error) {
    return value;
  }
}

async function extractError(response) {
  try {
    const data = await response.json();
    return data?.message;
  } catch (error) {
    return null;
  }
}

window.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const requestedRepo = params.get('repo');
  const requestedType = params.get('type');

  if (requestedType && (requestedType === 'prs' || requestedType === 'issues')) {
    typeSelect.value = requestedType;
  }

  if (requestedRepo) {
    const normalized = normalizeRepo(requestedRepo);
    if (normalized) {
      cache.prs = null;
      cache.issues = null;
      activeRepo = normalized;
      repoInput.value = requestedRepo.startsWith('http')
        ? requestedRepo
        : `https://github.com/${normalized}`;
      void loadItems(typeSelect.value);
    }
  }
});

function toggleSelect(disabled, message) {
  itemSelect.disabled = disabled;
  itemSelect.innerHTML = '';
  if (message) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = message;
    itemSelect.append(option);
  }
}
