const repoInput = document.getElementById('repoInput');
const typeSelect = document.getElementById('typeSelect');
const fetchBtn = document.getElementById('fetchBtn');
const itemSelect = document.getElementById('itemSelect');
const detailsContent = document.getElementById('detailsContent');
const highlights = document.getElementById('highlights');

let currentItems = [];

function normalizeRepoInput(value) {
  if (!value) {
    return null;
  }
  const trimmed = value.trim();
  const urlPattern = /^https?:\/\/github\.com\/([\w.-]+)\/([\w.-]+)\/?$/i;
  const shortPattern = /^([\w.-]+)\/([\w.-]+)$/;

  let match = trimmed.match(urlPattern);
  if (match) {
    return `${match[1]}/${match[2]}`;
  }

  match = trimmed.match(shortPattern);
  if (match) {
    return `${match[1]}/${match[2]}`;
  }

  return null;
}

function setLoading(loading) {
  fetchBtn.disabled = loading;
  fetchBtn.textContent = loading ? 'Loading…' : 'Fetch List';
}

function renderOptions() {
  itemSelect.innerHTML = '<option value="">-- Select an item --</option>';
  if (!currentItems.length) {
    itemSelect.disabled = true;
    highlights.textContent = '';
    return;
  }

  currentItems.forEach((item, index) => {
    const option = document.createElement('option');
    const number = item.number ? `#${item.number} ` : '';
    option.value = index;
    option.textContent = `${number}${item.title}`;
    if (item.labels && item.labels.some(label => label.name.toLowerCase() === 'bug')) {
      option.dataset.highlight = 'bug';
    }
    itemSelect.appendChild(option);
  });

  const bugged = currentItems.filter(item => item.labels && item.labels.some(label => label.name.toLowerCase() === 'bug'));
  if (bugged.length) {
    highlights.innerHTML = `⚠️ ${bugged.length} of the loaded items are labeled <strong>bug</strong>.`;
  } else {
    highlights.textContent = '';
  }

  itemSelect.disabled = false;
}

function formatStatus(item, type) {
  if (type === 'prs') {
    if (item.merged_at) {
      return 'Merged';
    }
    return item.state ? item.state.charAt(0).toUpperCase() + item.state.slice(1) : 'Unknown';
  }
  return item.state ? item.state.charAt(0).toUpperCase() + item.state.slice(1) : 'Unknown';
}

function formatDate(value) {
  if (!value) {
    return 'Unknown';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return 'Unknown';
  }
  return date.toLocaleString();
}

function renderDetails(index) {
  const type = typeSelect.value;
  const item = currentItems[index];
  if (!item) {
    detailsContent.textContent = 'Select a pull request or issue to see details.';
    return;
  }

  const wrapper = document.createElement('div');
  wrapper.innerHTML = '';

  const title = document.createElement('h3');
  title.textContent = item.title || 'Untitled';

  const status = document.createElement('p');
  status.className = 'detail-item';
  status.textContent = `Status: ${formatStatus(item, type)}`;

  const author = document.createElement('p');
  author.className = 'detail-item';
  author.textContent = `Author: ${item.user ? item.user.login : 'Unknown'}`;

  const created = document.createElement('p');
  created.className = 'detail-item';
  created.textContent = `Created: ${formatDate(item.created_at)}`;

  const updated = document.createElement('p');
  updated.className = 'detail-item';
  updated.textContent = `Updated: ${formatDate(item.updated_at)}`;

  const body = document.createElement('div');
  body.className = 'detail-item';
  const bodyTitle = document.createElement('strong');
  bodyTitle.textContent = 'Body:';
  const bodyContent = document.createElement('p');
  bodyContent.textContent = item.body?.trim() ? item.body : 'No description provided.';

  body.appendChild(bodyTitle);
  body.appendChild(bodyContent);

  wrapper.appendChild(title);
  wrapper.appendChild(status);
  wrapper.appendChild(author);
  wrapper.appendChild(created);
  wrapper.appendChild(updated);
  wrapper.appendChild(body);

  detailsContent.innerHTML = '';
  detailsContent.appendChild(wrapper);
}

async function fetchItems() {
  const repoValue = repoInput.value;
  const normalized = normalizeRepoInput(repoValue);
  if (!normalized) {
    alert('Please provide a valid GitHub repository URL or owner/repo format.');
    repoInput.focus();
    return;
  }

  const type = typeSelect.value;
  setLoading(true);
  itemSelect.disabled = true;
  itemSelect.innerHTML = '<option value="">Loading…</option>';
  detailsContent.textContent = 'Loading data…';
  highlights.textContent = '';

  try {
    const response = await fetch(`/api/${type}?repo=${encodeURIComponent(repoValue)}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Unable to load data from server.');
    }

    const data = await response.json();
    currentItems = Array.isArray(data.items) ? data.items : [];
    if (!currentItems.length) {
      alert('No items found for the selected repository.');
    }
    renderOptions();
    detailsContent.textContent = currentItems.length ? 'Select a pull request or issue to see details.' : 'No data to display.';
  } catch (error) {
    alert(error.message);
    currentItems = [];
    renderOptions();
    detailsContent.textContent = 'Could not load data from GitHub.';
  } finally {
    setLoading(false);
  }
}

fetchBtn.addEventListener('click', fetchItems);
itemSelect.addEventListener('change', (event) => {
  const index = event.target.value;
  if (index === '') {
    detailsContent.textContent = 'Select a pull request or issue to see details.';
    return;
  }
  renderDetails(Number(index));
});

repoInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    event.preventDefault();
    fetchItems();
  }
});

function applyQueryParameters() {
  const params = new URLSearchParams(window.location.search);
  const repoParam = params.get('repo');
  const typeParam = params.get('type');

  if (repoParam) {
    repoInput.value = repoParam;
  }

  if (typeParam) {
    const normalizedType = typeParam.toLowerCase();
    if (normalizedType === 'prs' || normalizedType === 'issues') {
      typeSelect.value = normalizedType;
    }
  }

  if (repoParam && typeParam) {
    fetchItems();
  }
}

applyQueryParameters();
