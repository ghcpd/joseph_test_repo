import {
  parseRepositoryUrl,
  fetchRepositoryItems,
  createSummary
} from '../src/github.js';

const repoInput = document.querySelector('#repoUrl');
const dataTypeSelect = document.querySelector('#dataType');
const itemsList = document.querySelector('#itemsList');
const detailsPanel = document.querySelector('#detailsPanel');
const fetchButton = document.querySelector('#fetchButton');
const statusMessage = document.querySelector('#statusMessage');

const cachedData = new Map();
let currentKey = '';
let currentType = dataTypeSelect.value;
let currentItems = [];

function updateStatus(message, type = 'error') {
  statusMessage.textContent = message;
  statusMessage.classList.remove('success');

  if (type === 'success') {
    statusMessage.classList.add('success');
  }
}

function clearList() {
  itemsList.innerHTML = '';
}

function clearDetails() {
  detailsPanel.innerHTML = '<p class="placeholder">Select an item to see its details.</p>';
}

function escapeHtml(text) {
  if (typeof text !== 'string') {
    return text;
  }

  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatDate(dateString) {
  if (!dateString) {
    return 'N/A';
  }

  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short'
    }).format(date);
  } catch (error) {
    console.warn('Unable to format date', error);
    return dateString;
  }
}

function renderList(items) {
  clearList();

  const fragment = document.createDocumentFragment();

  items.forEach((item) => {
    const option = document.createElement('option');
    option.value = String(item.number);
    option.textContent = `#${item.number} — ${item.title}`;

    if (item.isBug) {
      option.classList.add('option-bug');
    }

    fragment.appendChild(option);
  });

  itemsList.appendChild(fragment);
}

function renderItemDetails(item) {
  const statusLabel = item.state === 'merged' ? 'Merged' : item.state === 'open' ? 'Open' : 'Closed';

  detailsPanel.innerHTML = `
    <article>
      <header>
        <h2>${escapeHtml(item.title)}</h2>
        <div class="meta">
          <span><strong>Author:</strong> ${escapeHtml(item.user)}</span>
          <span><strong>Status:</strong> ${statusLabel}</span>
          <span><strong>Created:</strong> ${formatDate(item.created_at)}</span>
          <span><strong>Updated:</strong> ${formatDate(item.updated_at)}</span>
        </div>
      </header>
      <div class="body">${escapeHtml(item.body)}</div>
      <footer style="margin-top:1rem;">
        <a href="${item.html_url}" target="_blank" rel="noopener noreferrer">View on GitHub</a>
      </footer>
    </article>
  `;
}

function renderSummary(selectedItems) {
  const summary = createSummary(selectedItems);

  const summaryEntries = Object.entries(summary.states)
    .map(([state, count]) => `<span class="summary-item">${escapeHtml(state)}: ${count}</span>`)
    .join('');

  detailsPanel.innerHTML = `
    <div class="multi-summary">
      <h2>Combined Summary (${summary.count} items)</h2>
      <div class="meta">
        <strong>Authors:</strong> ${summary.authors.join(', ') || 'N/A'}
      </div>
      <div class="meta">
        <strong>Status breakdown:</strong>
        <div>${summaryEntries || 'N/A'}</div>
      </div>
      <div class="meta">
        <strong>Bug labeled items:</strong> ${summary.bugCount}
      </div>
      <ul>
        ${selectedItems
          .map(
            (item) => `
              <li>
                <a href="${item.html_url}" target="_blank" rel="noopener noreferrer">
                  #${item.number} — ${escapeHtml(item.title)}
                </a>
              </li>
            `
          )
          .join('')}
      </ul>
    </div>
  `;
}

function getCacheEntry(key) {
  if (!cachedData.has(key)) {
    cachedData.set(key, {
      pulls: null,
      issues: null,
      timestamp: Date.now()
    });
  }

  return cachedData.get(key);
}

function setCurrentItems(items) {
  currentItems = items;
}

function getSelectedItems() {
  const selectedNumbers = Array.from(itemsList.selectedOptions).map((option) => Number(option.value));
  return selectedNumbers
    .map((number) => currentItems.find((item) => item.number === number))
    .filter(Boolean);
}

async function handleFetch() {
  clearDetails();
  updateStatus('');

  let owner;
  let repo;

  try {
    ({ owner, repo } = parseRepositoryUrl(repoInput.value));
  } catch (error) {
    updateStatus(error.message);
    return;
  }

  const key = `${owner}/${repo}`;
  currentKey = key;
  currentType = dataTypeSelect.value;

  const cacheEntry = getCacheEntry(key);

  if (cacheEntry[currentType]) {
    setCurrentItems(cacheEntry[currentType]);
    renderList(cacheEntry[currentType]);
    updateStatus(`Loaded ${currentType === 'pulls' ? 'pull requests' : 'issues'} from cache.`, 'success');
    return;
  }

  try {
    fetchButton.disabled = true;
    updateStatus('Fetching data from GitHub…', 'success');

    const items = await fetchRepositoryItems(owner, repo, currentType);
    cacheEntry[currentType] = items;
    setCurrentItems(items);
    renderList(items);

    if (items.length === 0) {
      updateStatus('No matching items found for this selection.', 'success');
      clearDetails();
    } else {
      updateStatus(`Loaded ${items.length} ${currentType === 'pulls' ? 'pull requests' : 'issues'}.`, 'success');
    }
  } catch (error) {
    console.error(error);
    updateStatus(error.message || 'Failed to fetch data from GitHub.');
    clearList();
    clearDetails();
  } finally {
    fetchButton.disabled = false;
  }
}

function handleSelectionChange() {
  const selectedItems = getSelectedItems();

  if (selectedItems.length === 0) {
    clearDetails();
    return;
  }

  if (selectedItems.length > 1) {
    renderSummary(selectedItems);
    return;
  }

  renderItemDetails(selectedItems[0]);
}

dataTypeSelect.addEventListener('change', () => {
  currentType = dataTypeSelect.value;

  if (!currentKey) {
    return;
  }

  const cacheEntry = cachedData.get(currentKey);
  const cachedItemsForType = cacheEntry ? cacheEntry[currentType] : null;

  if (cachedItemsForType) {
    setCurrentItems(cachedItemsForType);
    renderList(cachedItemsForType);
    updateStatus(`Loaded ${currentType === 'pulls' ? 'pull requests' : 'issues'} from cache.`, 'success');
  } else {
    handleFetch();
  }
});

fetchButton.addEventListener('click', handleFetch);
itemsList.addEventListener('change', handleSelectionChange);

window.addEventListener('DOMContentLoaded', () => {
  clearDetails();
});
