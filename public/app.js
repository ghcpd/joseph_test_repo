const form = document.querySelector('#repo-form');
const repoInput = document.querySelector('#repo-url');
const dataTypeSelect = document.querySelector('#data-type');
const itemListSelect = document.querySelector('#item-list');
const infoPanel = document.querySelector('#info-panel');
const itemTitle = document.querySelector('#item-title');
const itemAuthor = document.querySelector('#item-author');
const itemStatus = document.querySelector('#item-status');
const itemCreated = document.querySelector('#item-created');
const itemUpdated = document.querySelector('#item-updated');
const itemBody = document.querySelector('#item-body');
const labelContainer = document.querySelector('#label-badges');
const fetchButton = document.querySelector('#fetch-button');

const repoPattern = /^[\w.-]+\/[\w.-]+$/;

let normalizedRepo = '';
let lastFetchType = 'prs';

const listCache = {
  prs: null,
  issues: null,
};

const detailCache = {
  prs: new Map(),
  issues: new Map(),
};

function resetCaches() {
  listCache.prs = null;
  listCache.issues = null;
  detailCache.prs.clear();
  detailCache.issues.clear();
}

function parseRepoInput(value) {
  if (!value || typeof value !== 'string') {
    return null;
  }

  const trimmed = value.trim();

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

function showError(message) {
  window.alert(message);
}

function setItemSelectState({ disabled, message }) {
  itemListSelect.disabled = disabled;
  itemListSelect.innerHTML = '';
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = message;
  itemListSelect.appendChild(placeholder);
}

function formatDate(date) {
  if (!date) {
    return '—';
  }
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) {
    return '—';
  }
  return parsed.toLocaleString();
}

function titleCase(value) {
  if (!value) {
    return '';
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function renderLabels(labels = []) {
  labelContainer.innerHTML = '';
  if (!labels.length) {
    return;
  }
  labels.forEach((label) => {
    const badge = document.createElement('span');
    badge.className = 'label-pill';
    badge.textContent = label;
    if (label.toLowerCase() === 'bug') {
      badge.classList.add('bug');
    }
    labelContainer.appendChild(badge);
  });
}

function renderDetails(item, type) {
  if (!item) {
    infoPanel.classList.add('hidden');
    return;
  }

  infoPanel.classList.remove('hidden');
  itemTitle.textContent = item.title || 'Untitled';
  itemAuthor.textContent = item.author || 'Unknown';

  let statusLabel = titleCase(item.state);
  if (type === 'prs') {
    if (item.merged) {
      statusLabel = 'Merged';
    } else if (item.state) {
      statusLabel = titleCase(item.state);
    }
  }

  itemStatus.textContent = statusLabel;
  itemCreated.textContent = formatDate(item.created_at);
  itemUpdated.textContent = formatDate(item.updated_at);
  itemBody.textContent = item.body || 'No description provided.';

  renderLabels(item.labels);

  const hasBugLabel = Array.isArray(item.labels)
    ? item.labels.some((label) => label.toLowerCase() === 'bug')
    : false;

  infoPanel.classList.toggle('has-bug', hasBugLabel);
}

async function fetchList(type) {
  const cache = listCache[type];
  if (cache && cache.repo === normalizedRepo) {
    populateItemSelect(cache.items);
    return;
  }

  lastFetchType = type;
  setItemSelectState({ disabled: true, message: 'Loading…' });
  fetchButton.disabled = true;

  try {
    const response = await fetch(`/api/${type}?repo=${encodeURIComponent(normalizedRepo)}`);
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(payload.error || 'Unable to fetch data from GitHub.');
    }

    const items = Array.isArray(payload.items) ? payload.items : [];
    listCache[type] = { repo: normalizedRepo, items };
    populateItemSelect(items);
  } catch (error) {
    setItemSelectState({ disabled: true, message: 'Failed to load items' });
    renderDetails(null);
    showError(error.message);
  } finally {
    fetchButton.disabled = false;
  }
}

async function fetchDetails(type, number) {
  if (!number) {
    renderDetails(null);
    return;
  }

  const cacheKey = `${normalizedRepo}::${number}`;
  const detailMap = detailCache[type];

  if (detailMap.has(cacheKey)) {
    renderDetails(detailMap.get(cacheKey), type);
    return;
  }

  try {
    const response = await fetch(
      `/api/${type}?repo=${encodeURIComponent(normalizedRepo)}&number=${encodeURIComponent(number)}`,
    );
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(payload.error || 'Unable to fetch item details.');
    }

    detailMap.set(cacheKey, payload.item);
    renderDetails(payload.item, type);
  } catch (error) {
    renderDetails(null);
    showError(error.message);
  }
}

function populateItemSelect(items) {
  itemListSelect.innerHTML = '';

  if (!items.length) {
    setItemSelectState({ disabled: true, message: 'No items found' });
    return;
  }

  itemListSelect.disabled = false;

  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'Select a PR or Issue';
  placeholder.disabled = true;
  placeholder.hidden = true;
  itemListSelect.appendChild(placeholder);

  items.forEach((item) => {
    const option = document.createElement('option');
    option.value = item.number;
    option.textContent = `#${item.number} • ${item.title}`;
    if (Array.isArray(item.labels) && item.labels.some((label) => label.toLowerCase() === 'bug')) {
      option.classList.add('bugged');
    }
    itemListSelect.appendChild(option);
  });

  const firstItem = items[0];
  if (firstItem) {
    itemListSelect.value = String(firstItem.number);
    fetchDetails(dataTypeSelect.value, String(firstItem.number));
  } else {
    renderDetails(null);
  }
}

function handleFormSubmit(event) {
  event.preventDefault();
  const parsed = parseRepoInput(repoInput.value);

  if (!parsed) {
    showError('Please enter a valid GitHub repository (owner/repo or https://github.com/owner/repo).');
    return;
  }

  if (parsed !== normalizedRepo) {
    normalizedRepo = parsed;
    resetCaches();
  }

  fetchList(dataTypeSelect.value);
}

function handleTypeChange(event) {
  if (!normalizedRepo) {
    return;
  }
  fetchList(event.target.value);
}

function handleItemSelection(event) {
  const value = event.target.value;
  if (!value) {
    renderDetails(null);
    return;
  }
  fetchDetails(dataTypeSelect.value, value);
}

form.addEventListener('submit', handleFormSubmit);
dataTypeSelect.addEventListener('change', handleTypeChange);
itemListSelect.addEventListener('change', handleItemSelection);

document.addEventListener('DOMContentLoaded', () => {
  setItemSelectState({ disabled: true, message: 'No data loaded' });
  infoPanel.classList.add('hidden');
});
