const repoInput = document.getElementById('repo-url');
const dataTypeSelect = document.getElementById('data-type');
const itemsSelect = document.getElementById('items');
const statusMessage = document.getElementById('status-message');
const errorMessage = document.getElementById('error-message');
const loadButton = document.getElementById('load-button');
const detailsContainer = document.getElementById('details-container');
const detailTemplate = document.getElementById('detail-template');
const summaryContainer = document.getElementById('summary');

const detailCache = new Map();
let currentRepo = '';
let currentList = [];

function parseRepo(input) {
  if (!input) {
    throw new Error('Repository URL is required.');
  }
  const trimmed = input.trim();
  const directPattern = /^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/;
  if (directPattern.test(trimmed)) {
    return trimmed;
  }

  const urlPattern = /^https?:\/\/(?:www\.)?github\.com\/(?!user|settings|orgs)([^\/\s]+)\/([^\/\s]+)(?:\/.+)?$/i;
  const match = trimmed.match(urlPattern);
  if (!match || !match[1] || !match[2]) {
    throw new Error('Please enter a valid GitHub repository URL (https://github.com/owner/repo)');
  }

  return `${match[1]}/${match[2]}`;
}

function setLoading(message) {
  statusMessage.textContent = message;
  errorMessage.textContent = '';
}

function setError(message) {
  errorMessage.textContent = message;
  statusMessage.textContent = '';
  alert(message);
}

function clearMessages() {
  statusMessage.textContent = '';
  errorMessage.textContent = '';
}

function clearList() {
  itemsSelect.innerHTML = '';
}

function clearDetails() {
  detailsContainer.innerHTML = '';
  summaryContainer.textContent = '';
}

function optionLabel(item) {
  const prefix = item.type === 'issues' || item.isIssue ? 'Issue' : 'PR';
  return `#${item.number} ${item.title} (${prefix})`;
}

function highlightOption(optionElement, item) {
  if (Array.isArray(item.labels) && item.labels.some((label) => label.toLowerCase() === 'bug')) {
    optionElement.classList.add('highlight');
  }
}

function populateList(items) {
  clearList();
  items.forEach((item) => {
    const option = document.createElement('option');
    option.value = item.number;
    option.textContent = optionLabel(item);
    highlightOption(option, item);
    itemsSelect.appendChild(option);
  });
  if (items.length === 0) {
    const placeholder = document.createElement('option');
    placeholder.disabled = true;
    placeholder.textContent = 'No items found';
    itemsSelect.appendChild(placeholder);
  }
}

function formatDate(value) {
  if (!value) return 'Unknown';
  return new Date(value).toLocaleString();
}

function getStatus(detail) {
  if (detail.type === 'pull_request') {
    if (detail.merged) return 'merged';
    return detail.state;
  }
  return detail.state;
}

function renderSummary(details) {
  if (details.length < 2) {
    summaryContainer.textContent = '';
    return;
  }

  const bugCount = details.filter((detail) =>
    Array.isArray(detail.labels) && detail.labels.some((label) => label.toLowerCase() === 'bug')
  ).length;
  const openCount = details.filter((detail) => detail.state === 'open').length;
  summaryContainer.textContent = `Summary: ${details.length} selected, ${openCount} open, ${bugCount} labeled as "bug".`;
}

function renderDetail(detail) {
  const clone = detailTemplate.content.cloneNode(true);
  const article = clone.querySelector('.detail');
  const titleEl = clone.querySelector('.detail-title');
  const metaFields = clone.querySelectorAll('[data-field]');

  titleEl.textContent = `#${detail.number} ${detail.title}`;

  metaFields.forEach((field) => {
    const name = field.getAttribute('data-field');
    switch (name) {
      case 'author':
        field.textContent = detail.author;
        break;
      case 'status':
        field.textContent = getStatus(detail);
        break;
      case 'created':
        field.textContent = formatDate(detail.created_at);
        break;
      case 'updated':
        field.textContent = formatDate(detail.updated_at);
        break;
      case 'labels':
        field.textContent = Array.isArray(detail.labels) && detail.labels.length > 0 ? detail.labels.join(', ') : 'None';
        break;
      case 'merged':
        field.textContent = detail.merged ? 'Yes' : 'No';
        break;
      default:
        field.textContent = detail[name] || '';
    }
  });

  const mergedRow = clone.querySelector('.merged');
  if (detail.type === 'pull_request') {
    mergedRow.hidden = false;
  }

  const extra = clone.querySelector('.extra');
  if (detail.type === 'pull_request') {
    extra.innerHTML = `<strong>Diff:</strong> +${detail.additions} / -${detail.deletions}, files changed: ${detail.changed_files}`;
  } else {
    extra.innerHTML = `<strong>Comments:</strong> ${detail.comments ?? 0}`;
  }

  const body = clone.querySelector('.body');
  body.textContent = detail.body ? detail.body : 'No description provided.';

  if (Array.isArray(detail.labels) && detail.labels.some((label) => label.toLowerCase() === 'bug')) {
    article.classList.add('highlight');
  }

  detailsContainer.appendChild(clone);
}

function renderDetails(details) {
  clearDetails();
  renderSummary(details);
  details.forEach((detail) => renderDetail(detail));
}

async function fetchList(repo, type) {
  const endpoint = type === 'issues' ? '/api/issues' : '/api/prs';
  const url = `${endpoint}?repo=${encodeURIComponent(repo)}`;
  const response = await fetch(url);
  if (!response.ok) {
    const data = await response.json().catch(() => ({ error: response.statusText }));
    const error = data.error || data.message || 'Failed to fetch data from server.';
    throw new Error(error);
  }
  return response.json();
}

async function fetchDetail(repo, type, number) {
  const cacheKey = `${repo}:${type}:${number}`;
  if (detailCache.has(cacheKey)) {
    return detailCache.get(cacheKey);
  }
  const endpoint = type === 'issues' ? '/api/issues' : '/api/prs';
  const response = await fetch(`${endpoint}/${number}?repo=${encodeURIComponent(repo)}`);
  if (!response.ok) {
    const data = await response.json().catch(() => ({ error: response.statusText }));
    const error = data.error || data.message || 'Failed to fetch detail.';
    throw new Error(error);
  }
  const detail = await response.json();
  detailCache.set(cacheKey, detail);
  return detail;
}

async function loadData({ silent = false } = {}) {
  try {
    clearMessages();
    clearList();
    clearDetails();
    detailCache.clear();

    const repo = parseRepo(repoInput.value);
    currentRepo = repo;

    setLoading('Loading data from GitHub...');
    const type = dataTypeSelect.value === 'issues' ? 'issues' : 'pulls';
    const data = await fetchList(repo, type);
    currentList = data;
    populateList(data);

    if (data.length > 0) {
      itemsSelect.selectedIndex = 0;
      await handleSelection();
    }

    statusMessage.textContent = `Loaded ${data.length} item(s) from ${type === 'pulls' ? 'Pull Requests' : 'Issues'} endpoint.`;
  } catch (error) {
    if (silent) {
      statusMessage.textContent = '';
      errorMessage.textContent = error.message;
    } else {
      setError(error.message);
    }
    currentRepo = '';
    currentList = [];
  }
}

async function handleSelection() {
  if (!currentRepo) {
    return;
  }

  const selectedNumbers = Array.from(itemsSelect.selectedOptions).map((option) => Number(option.value)).filter((value) => Number.isInteger(value));
  if (selectedNumbers.length === 0) {
    clearDetails();
    return;
  }

  setLoading('Loading selected item details...');
  try {
    const type = dataTypeSelect.value === 'issues' ? 'issues' : 'pulls';
    const details = await Promise.all(selectedNumbers.map((number) => fetchDetail(currentRepo, type, number)));
    renderDetails(details);
    statusMessage.textContent = '';
  } catch (error) {
    setError(error.message);
  }
}

loadButton.addEventListener('click', async () => {
  try {
    await loadData();
  } catch (error) {
    setError(error.message);
  }
});

dataTypeSelect.addEventListener('change', async () => {
  if (!currentRepo) {
    return;
  }
  await loadData();
});

itemsSelect.addEventListener('change', handleSelection);

// Prefill with an example repo to help users
repoInput.value = 'https://github.com/github/docs';


loadData({ silent: true }).catch(() => {});
