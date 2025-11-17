const repoForm = document.getElementById('repo-form');
const repoInput = document.getElementById('repo-input');
const typeSelect = document.getElementById('type-select');
const itemSelect = document.getElementById('item-select');
const summary = document.getElementById('summary');
const detailTitle = document.getElementById('detail-title');
const detailAuthor = document.getElementById('detail-author');
const detailStatus = document.getElementById('detail-status');
const detailCreated = document.getElementById('detail-created');
const detailUpdated = document.getElementById('detail-updated');
const detailBody = document.getElementById('detail-body');
const labelsContainer = document.getElementById('labels');
const toast = document.getElementById('toast');

let currentRepo = '';
let currentType = typeSelect.value;
let currentItems = [];
const detailCache = new Map();

function parseRepoInput(value) {
  if (!value) {
    return null;
  }
  const trimmed = value.trim();
  const repoPattern = /^[\w.-]+\/[\w.-]+$/;
  if (repoPattern.test(trimmed)) {
    return trimmed;
  }
  const match = trimmed.match(/^https?:\/\/github\.com\/([^\s/]+\/[^\s/?#]+)/i);
  if (!match) {
    return null;
  }
  const repoPart = match[1].replace(/\.git$/, '');
  return repoPattern.test(repoPart) ? repoPart : null;
}

function showToast(message, isError = true) {
  toast.textContent = message;
  toast.className = `toast ${isError ? 'error' : 'success'}`;
  toast.classList.add('visible');
  window.setTimeout(() => {
    toast.classList.remove('visible');
  }, 4000);
}

function formatDate(value) {
  if (!value) {
    return '—';
  }
  try {
    return new Date(value).toLocaleString();
  } catch (error) {
    return value;
  }
}

function buildSummary(selectedItems) {
  if (selectedItems.length <= 1) {
    summary.textContent = '';
    return;
  }

  const info = selectedItems.map(item => {
    const typeLabel = currentType === 'prs' ? 'PR' : 'Issue';
    const merged = item.merged_at ? 'Merged' : undefined;
    const status = merged || (item.state ? item.state.toUpperCase() : 'Unknown');
    return `${typeLabel} #${item.number}: ${status}`;
  });

  summary.innerHTML = `<strong>Multi-selection summary (${selectedItems.length} items)</strong><br>${info.join('<br>')}`;
}

function highlightSelection(option, item) {
  if (!item.labels) {
    return;
  }
  const hasBug = item.labels.some(label => label.name.toLowerCase() === 'bug');
  if (hasBug) {
    option.classList.add('has-bug');
  }
}

async function displayDetail(number) {
  if (!number) {
    return;
  }

  const key = `${currentType}:${currentRepo}:${number}`;
  let detail = detailCache.get(key);

  if (!detail) {
    try {
      const response = await fetch(`/api/${currentType}/${number}?repo=${encodeURIComponent(currentRepo)}`);
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Unable to fetch details');
      }
      detail = await response.json();
      detailCache.set(key, detail);
    } catch (error) {
      showToast(error.message || 'Unable to fetch details.');
      return;
    }
  }

  const status = currentType === 'prs'
    ? (detail.merged_at ? 'Merged' : detail.state ? detail.state.charAt(0).toUpperCase() + detail.state.slice(1) : 'Unknown')
    : detail.state ? detail.state.charAt(0).toUpperCase() + detail.state.slice(1) : 'Unknown';

  detailTitle.textContent = detail.title || `#${number}`;
  detailAuthor.textContent = (detail.user && detail.user.login) || 'Unknown';
  detailStatus.textContent = status;
  detailCreated.textContent = formatDate(detail.created_at);
  detailUpdated.textContent = formatDate(detail.updated_at);
  detailBody.textContent = detail.body || 'No description provided.';

  labelsContainer.innerHTML = '';
  if (Array.isArray(detail.labels) && detail.labels.length > 0) {
    const list = document.createElement('div');
    list.className = 'labels';
    detail.labels.forEach(label => {
      const span = document.createElement('span');
      span.textContent = label.name;
      span.className = 'label';
      if (label.name.toLowerCase() === 'bug') {
        span.classList.add('label-bug');
      }
      list.appendChild(span);
    });
    labelsContainer.appendChild(list);
  }
}

function populateDropdown(items) {
  itemSelect.innerHTML = '';
  const fragment = document.createDocumentFragment();

  items.forEach(item => {
    const option = document.createElement('option');
    option.value = String(item.number);
    option.textContent = `#${item.number} - ${item.title || 'Untitled'}`;
    option.dataset.state = item.state;
    option.dataset.merged = item.merged_at ? 'true' : 'false';
    highlightSelection(option, item);
    fragment.appendChild(option);
  });

  itemSelect.appendChild(fragment);

  if (items.length > 0) {
    itemSelect.selectedIndex = 0;
    displayDetail(items[0].number);
  } else {
    detailTitle.textContent = 'No results';
    detailAuthor.textContent = '—';
    detailStatus.textContent = '—';
    detailCreated.textContent = '—';
    detailUpdated.textContent = '—';
    detailBody.textContent = '';
    labelsContainer.innerHTML = '';
  }
}

async function fetchItems() {
  const repo = parseRepoInput(repoInput.value);
  if (!repo) {
    showToast('Invalid repository URL. Please use https://github.com/user/repo or owner/repo format.');
    return;
  }

  currentRepo = repo;
  detailCache.clear();

  try {
    const response = await fetch(`/api/${currentType}?repo=${encodeURIComponent(currentRepo)}`);
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || 'Unable to fetch data.');
    }
    const data = await response.json();
    currentItems = Array.isArray(data) ? data : [];
    populateDropdown(currentItems);
    const fetchedType = currentType === 'prs' ? 'pull requests' : 'issues';
    showToast(`Fetched ${currentItems.length} ${fetchedType}.`, false);
  } catch (error) {
    populateDropdown([]);
    showToast(error.message || 'Unable to fetch data.');
  }
}

repoForm.addEventListener('submit', event => {
  event.preventDefault();
  fetchItems();
});

typeSelect.addEventListener('change', () => {
  currentType = typeSelect.value;
  if (currentRepo) {
    fetchItems();
  }
});

itemSelect.addEventListener('change', async () => {
  const selectedNumbers = Array.from(itemSelect.selectedOptions).map(option => parseInt(option.value, 10));
  const selectedItems = currentItems.filter(item => selectedNumbers.includes(item.number));
  if (selectedItems.length > 0) {
    await displayDetail(selectedItems[selectedItems.length - 1].number);
  }
  buildSummary(selectedItems);
});

window.addEventListener('load', () => {
  itemSelect.multiple = true;
});
