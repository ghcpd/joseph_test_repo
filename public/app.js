const repoForm = document.getElementById('repoForm');
const repoInput = document.getElementById('repoInput');
const typeSelect = document.getElementById('dataTypeSelect');
const itemSelect = document.getElementById('itemSelect');
const itemDetails = document.getElementById('itemDetails');
const fetchButton = document.getElementById('fetchButton');

let currentItems = [];
let currentRepo = '';

const ENDPOINTS = {
  prs: '/api/prs',
  issues: '/api/issues'
};

repoForm.addEventListener('submit', (event) => {
  event.preventDefault();
  fetchRepositoryData();
});

typeSelect.addEventListener('change', () => {
  if (currentRepo) {
    fetchRepositoryData();
  }
});

itemSelect.addEventListener('change', () => {
  const selectedNumber = itemSelect.value;
  const target = currentItems.find((item) => String(item.number) === selectedNumber);
  renderDetails(target);
});

function parseRepositoryUrl(input) {
  if (!input) {
    return null;
  }

  const trimmed = input.trim();
  const shortPattern = /^([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)$/;
  const fullPattern = /^https?:\/\/github\.com\/([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)(?:\/)?$/i;

  const shortMatch = trimmed.match(shortPattern);
  if (shortMatch) {
    return `${shortMatch[1]}/${shortMatch[2]}`;
  }

  const fullMatch = trimmed.match(fullPattern);
  if (fullMatch) {
    return `${fullMatch[1]}/${fullMatch[2]}`;
  }

  return null;
}

async function fetchRepositoryData() {
  const repoFullName = parseRepositoryUrl(repoInput.value);

  if (!repoFullName) {
    alert('Please provide a valid GitHub repository URL (https://github.com/owner/repo).');
    itemSelect.disabled = true;
    resetDetails('Choose a pull request or issue to see details.');
    return;
  }

  const type = typeSelect.value;
  const endpoint = ENDPOINTS[type];

  if (!endpoint) {
    alert('Invalid selection.');
    return;
  }

  currentRepo = repoFullName;
  setLoadingState(true);
  resetDetails('Loading data from GitHub...');

  try {
    const response = await fetch(`${endpoint}?repo=${encodeURIComponent(repoFullName)}`);
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || 'Unknown server error.');
    }

    currentItems = Array.isArray(payload) ? payload : [];

    if (currentItems.length === 0) {
      itemSelect.innerHTML = '<option value="">No items found.</option>';
      itemSelect.disabled = true;
      resetDetails('No pull requests or issues available for this selection.');
      return;
    }

    populateItemDropdown(currentItems);
    renderDetails(currentItems[0]);
  } catch (error) {
    alert(error.message || 'An unexpected error occurred while contacting the server.');
    itemSelect.disabled = true;
    resetDetails('Unable to load data. Try again later.');
  } finally {
    setLoadingState(false);
  }
}

function populateItemDropdown(items) {
  itemSelect.innerHTML = '<option value="">Select an item...</option>';
  items.forEach((item) => {
    const option = document.createElement('option');
    option.value = String(item.number);
    option.textContent = `#${item.number} – ${item.title}`;
    itemSelect.appendChild(option);
  });
  itemSelect.disabled = false;
  itemSelect.value = String(items[0].number);
}

function resetDetails(message) {
  itemDetails.className = 'card empty';
  itemDetails.textContent = message;
}

function renderDetails(item) {
  if (!item) {
    resetDetails('Choose a pull request or issue to see details.');
    return;
  }

  itemDetails.className = 'card';
  itemDetails.innerHTML = '';

  const isBug = (item.labels || []).some((label) => label.toLowerCase() === 'bug');
  if (isBug) {
    itemDetails.classList.add('has-bug');
  }

  const header = document.createElement('h3');
  header.textContent = `${item.title} (#${item.number})`;

  const metaRow = document.createElement('div');
  metaRow.className = 'row';

  const authorSpan = document.createElement('span');
  authorSpan.innerHTML = `<strong>Author:</strong> ${item.author}`;

  const statusBadge = document.createElement('span');
  const normalizedStatus = normalizeStatus(item.state);
  statusBadge.className = `badge status-${normalizedStatus}`;
  statusBadge.textContent = normalizedStatus;

  metaRow.append(authorSpan, statusBadge);

  const metaList = document.createElement('div');
  metaList.className = 'meta-list';
  metaList.innerHTML = `
    <span><strong>Created:</strong> ${formatDate(item.created_at)}</span>
    <span><strong>Updated:</strong> ${formatDate(item.updated_at)}</span>
    <a href="${item.html_url}" target="_blank" rel="noopener noreferrer">View on GitHub</a>
  `;

  const labelsContainer = document.createElement('div');
  labelsContainer.className = 'row';
  labelsContainer.style.flexWrap = 'wrap';

  if (item.labels && item.labels.length > 0) {
    item.labels.forEach((label) => {
      const badge = document.createElement('span');
      badge.className = 'badge';
      if (label.toLowerCase() === 'bug') {
        badge.classList.add('bug');
      }
      badge.textContent = label;
      labelsContainer.appendChild(badge);
    });
  } else {
    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = 'No Labels';
    labelsContainer.appendChild(badge);
  }

  const bodySection = document.createElement('div');
  const bodyTitle = document.createElement('strong');
  bodyTitle.textContent = 'Description';

  const bodyContent = document.createElement('p');
  bodyContent.textContent = item.body ? item.body : 'No description provided.';

  bodySection.append(bodyTitle, bodyContent);

  itemDetails.append(header, metaRow, labelsContainer, metaList, bodySection);
}

function formatDate(value) {
  if (!value) {
    return 'Unknown';
  }
  try {
    return new Date(value).toLocaleString();
  } catch (err) {
    return value;
  }
}

function normalizeStatus(status) {
  if (!status) {
    return 'unknown';
  }
  const lower = status.toLowerCase();
  if (lower === 'closed' || lower === 'open' || lower === 'merged') {
    return lower;
  }
  return lower;
}

function setLoadingState(isLoading) {
  fetchButton.disabled = isLoading;
  fetchButton.textContent = isLoading ? 'Loading…' : 'Fetch';
  if (isLoading) {
    itemSelect.disabled = true;
  }
}
