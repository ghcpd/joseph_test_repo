const repoForm = document.getElementById('repo-form');
const repoInput = document.getElementById('repo-url');
const dataTypeSelect = document.getElementById('data-type');
const itemSelect = document.getElementById('item-select');
const statusBanner = document.getElementById('status');

const detailTitle = document.getElementById('detail-title');
const detailAuthor = document.getElementById('detail-author');
const detailStatus = document.getElementById('detail-status');
const detailCreated = document.getElementById('detail-created');
const detailUpdated = document.getElementById('detail-updated');
const detailBody = document.getElementById('detail-body');

const REPO_URL_PATTERN = /^https:\/\/github\.com\/(?!-)([\w.-]+)\/(?!-)([\w.-]+)(?:\.git)?\/?$/i;

function parseRepoUrl(url) {
  const trimmed = url.trim();
  const match = trimmed.match(REPO_URL_PATTERN);
  if (!match) {
    return null;
  }
  return `${match[1]}/${match[2]}`;
}

function showStatus(message, variant = 'info') {
  statusBanner.textContent = message;
  statusBanner.style.display = 'block';
  statusBanner.dataset.variant = variant;
}

function clearStatus() {
  statusBanner.textContent = '';
  statusBanner.style.display = 'none';
  statusBanner.dataset.variant = '';
}

function resetDetails() {
  detailTitle.textContent = 'No item selected';
  detailAuthor.textContent = 'Author: —';
  detailStatus.textContent = '—';
  detailCreated.textContent = '—';
  detailUpdated.textContent = '—';
  detailBody.textContent = 'Choose a pull request or issue to see its description.';
}

async function fetchItems(repo, type) {
  const endpoint = type === 'pull-requests' ? 'pull-requests' : 'issues';
  showStatus('Fetching data from GitHub…');
  itemSelect.innerHTML = '';
  itemSelect.disabled = true;
  resetDetails();

  try {
    const response = await fetch(`/api/${endpoint}?repo=${encodeURIComponent(repo)}`);
    if (!response.ok) {
      const { error } = await response.json();
      throw new Error(error || 'Unable to retrieve data from GitHub.');
    }

    const data = await response.json();
    if (data.length === 0) {
      showStatus('No results found for this repository.', 'warning');
      return;
    }

    const fragment = document.createDocumentFragment();
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = `Select a ${type === 'pull-requests' ? 'pull request' : 'issue'}…`;
    fragment.appendChild(defaultOption);

    data.forEach((item) => {
      const option = document.createElement('option');
      option.value = item.number;
      option.textContent = `#${item.number} · ${item.title}`;
      if (item.state === 'open') {
        option.dataset.state = 'open';
      }
      fragment.appendChild(option);
    });

    itemSelect.appendChild(fragment);
    itemSelect.disabled = false;
    clearStatus();

    if (itemSelect.options.length > 1) {
      itemSelect.selectedIndex = 1;
      fetchDetails(repo, type, itemSelect.value);
    }
  } catch (error) {
    showStatus(error.message, 'error');
  }
}

function formatTimestamp(timestamp) {
  if (!timestamp) {
    return '—';
  }

  try {
    return new Date(timestamp).toLocaleString();
  } catch (error) {
    return timestamp;
  }
}

async function fetchDetails(repo, type, number) {
  if (!number) {
    resetDetails();
    return;
  }

  const endpoint = type === 'pull-requests' ? 'pull-requests' : 'issues';
  showStatus('Fetching details…');

  try {
    const response = await fetch(`/api/${endpoint}/${number}?repo=${encodeURIComponent(repo)}`);
    if (!response.ok) {
      const { error } = await response.json();
      throw new Error(error || 'Unable to retrieve item details.');
    }

    const detail = await response.json();

    detailTitle.textContent = detail.title;
    detailAuthor.textContent = `Author: ${detail.user}`;

    if (type === 'pull-requests') {
      detailStatus.textContent = detail.merged ? 'Merged' : detail.state;
    } else {
      detailStatus.textContent = detail.state;
    }

    detailCreated.textContent = formatTimestamp(detail.created_at);
    detailUpdated.textContent = formatTimestamp(detail.updated_at);
    detailBody.textContent = detail.body ? detail.body.trim() : 'No description provided.';
    clearStatus();
  } catch (error) {
    showStatus(error.message, 'error');
  }
}

repoForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const repoValue = repoInput.value;
  const parsed = parseRepoUrl(repoValue);

  if (!parsed) {
    alert('Please provide a valid GitHub repository URL (e.g., https://github.com/owner/repo).');
    repoInput.focus();
    return;
  }

  fetchItems(parsed, dataTypeSelect.value);
  repoForm.dataset.repo = parsed;
});

dataTypeSelect.addEventListener('change', () => {
  const repo = repoForm.dataset.repo;
  if (!repo) {
    return;
  }
  fetchItems(repo, dataTypeSelect.value);
});

itemSelect.addEventListener('change', () => {
  const repo = repoForm.dataset.repo;
  if (!repo) {
    return;
  }
  const number = itemSelect.value;
  fetchDetails(repo, dataTypeSelect.value, number);
});

document.addEventListener('DOMContentLoaded', () => {
  const defaultRepo = repoInput.dataset.defaultRepo;
  if (!defaultRepo) {
    resetDetails();
    return;
  }

  const parsed = parseRepoUrl(defaultRepo);
  if (!parsed) {
    resetDetails();
    return;
  }

  repoInput.value = defaultRepo;
  repoForm.dataset.repo = parsed;
  fetchItems(parsed, dataTypeSelect.value);
});
