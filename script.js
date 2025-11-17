const repoUrlInput = document.getElementById("repo-url");
const dataTypeSelect = document.getElementById("data-type");
const fetchButton = document.getElementById("fetch-btn");
const itemListSelect = document.getElementById("item-list");
const detailsPanel = document.getElementById("details");

let cachedItems = [];
const detailCache = new Map();

fetchButton.addEventListener("click", handleFetchClick);
itemListSelect.addEventListener("change", handleItemSelection);

function parseRepositoryUrl(rawUrl) {
  if (!rawUrl) return null;

  let urlInstance;
  try {
    urlInstance = new URL(rawUrl.trim());
  } catch (error) {
    return null;
  }

  if (urlInstance.protocol !== "https:" || urlInstance.hostname !== "github.com") {
    return null;
  }

  const cleanedPath = urlInstance.pathname
    .replace(/\.git$/, "")
    .replace(/\/$/, "")
    .trim();

  const segments = cleanedPath.split("/").filter(Boolean);
  if (segments.length < 2) {
    return null;
  }

  const [owner, repo] = segments;
  if (!owner || !repo) {
    return null;
  }

  return { owner, repo };
}

async function handleFetchClick() {
  const parsed = parseRepositoryUrl(repoUrlInput.value);
  if (!parsed) {
    window.alert("Please enter a valid GitHub repository URL in the format https://github.com/owner/repo.");
    return;
  }

  toggleFetchState(true);
  const { owner, repo } = parsed;
  const dataType = dataTypeSelect.value;

  try {
    const items = await fetchRepositoryItems(owner, repo, dataType);
    cachedItems = items;
    detailCache.clear();

    if (!items.length) {
      resetItemList("No items found for the selected type.");
      renderPlaceholder("No data to display. Try another repository or data type.");
    } else {
      populateItemList(items, dataType);
      renderPlaceholder("Select an item from the list to view details.");
    }
  } catch (error) {
    console.error(error);
    window.alert(error.message || "Failed to fetch items from GitHub. Please try again.");
    resetItemList("Fetch failed. Check repository URL.");
    renderPlaceholder("Unable to load items. Please try again.");
  } finally {
    toggleFetchState(false);
  }
}

function toggleFetchState(isLoading) {
  fetchButton.disabled = isLoading;
  fetchButton.textContent = isLoading ? "Loading..." : "Fetch List";
}

async function fetchRepositoryItems(owner, repo, dataType) {
  const endpoint = `https://api.github.com/repos/${owner}/${repo}/${dataType}?per_page=50&state=all`;

  const response = await fetch(endpoint, {
    headers: {
      Accept: "application/vnd.github+json",
    },
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Repository not found. Please double-check the owner and repository name.");
    }

    if (response.status === 403) {
      throw new Error("GitHub API rate limit reached. Please wait a moment and try again.");
    }

    throw new Error(`GitHub API request failed with status ${response.status}.`);
  }

  const payload = await response.json();
  if (!Array.isArray(payload)) {
    throw new Error("Unexpected response from GitHub API.");
  }

  return payload.map((item) => ({
    id: item.id,
    number: item.number,
    title: item.title,
    state: item.state,
    created_at: item.created_at,
    updated_at: item.updated_at,
    user: item.user,
    html_url: item.html_url,
    body: item.body || "",
    labels: item.labels || [],
    detail_url: item.url,
    type: dataType,
  }));
}

function resetItemList(message) {
  itemListSelect.innerHTML = "";
  const placeholderOption = document.createElement("option");
  placeholderOption.textContent = message;
  placeholderOption.disabled = true;
  placeholderOption.selected = true;
  itemListSelect.appendChild(placeholderOption);
  itemListSelect.disabled = true;
}

function populateItemList(items, dataType) {
  itemListSelect.innerHTML = "";
  const placeholderOption = document.createElement("option");
  placeholderOption.textContent = `Select a ${dataType === "pulls" ? "pull request" : "issue"}`;
  placeholderOption.disabled = true;
  placeholderOption.selected = true;
  itemListSelect.appendChild(placeholderOption);

  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = String(item.id);
    const hasBugLabel = item.labels.some((label) => label.name && label.name.toLowerCase() === "bug");
    option.textContent = `#${item.number} • ${item.title}${hasBugLabel ? " 🐞" : ""}`;
    if (hasBugLabel) {
      option.classList.add("option-bug");
    }
    itemListSelect.appendChild(option);
  });

  itemListSelect.disabled = false;
}

async function handleItemSelection() {
  const selectedId = itemListSelect.value;
  const selectedItem = cachedItems.find((item) => String(item.id) === selectedId);

  if (!selectedItem) {
    return;
  }

  try {
    const detail = await loadItemDetail(selectedItem);
    renderItemDetails(detail);
  } catch (error) {
    console.error(error);
    window.alert("Unable to load details for the selected item.");
  }
}

async function loadItemDetail(item) {
  if (detailCache.has(item.id)) {
    return detailCache.get(item.id);
  }

  if (item.type !== "pulls") {
    detailCache.set(item.id, item);
    return item;
  }

  const response = await fetch(item.detail_url, {
    headers: {
      Accept: "application/vnd.github+json",
    },
  });

  if (!response.ok) {
    throw new Error(`Unable to fetch pull request details (status ${response.status}).`);
  }

  const data = await response.json();
  const detailedItem = {
    ...item,
    state: data.state,
    merged_at: data.merged_at,
    body: data.body || item.body,
    labels: data.labels || item.labels,
  };

  detailCache.set(item.id, detailedItem);
  return detailedItem;
}

function renderPlaceholder(message) {
  detailsPanel.innerHTML = `<p class="placeholder">${message}</p>`;
}

function renderItemDetails(item) {
  const title = escapeHtml(item.title || "(No title)");
  const author = item.user?.login ? escapeHtml(item.user.login) : "Unknown";
  const created = new Date(item.created_at).toLocaleString();
  const updated = new Date(item.updated_at).toLocaleString();
  const body = item.body ? escapeHtml(item.body) : "No description provided.";

  let statusText = item.state;
  let statusClass = "status-open";

  if (item.type === "pulls") {
    if (item.state === "closed" && item.merged_at) {
      statusText = "merged";
      statusClass = "status-merged";
    } else if (item.state === "closed") {
      statusClass = "status-closed";
    }
  } else if (item.state === "closed") {
    statusClass = "status-closed";
  }

  const labelsMarkup = (item.labels || [])
    .map((label) => `<span style="background:#${label.color || "e5e7eb"}">${escapeHtml(label.name)}</span>`)
    .join("");

  detailsPanel.innerHTML = `
    <h2>${title}</h2>
    <div class="metadata">
      <span>Author: ${author}</span>
      <span class="${statusClass}">Status: ${statusText}</span>
      <span>Created: ${created}</span>
      <span>Updated: ${updated}</span>
    </div>
    <div class="metadata">
      ${labelsMarkup || "<span>No labels</span>"}
    </div>
    <div class="body">${body}</div>
    <p><a href="${item.html_url}" target="_blank" rel="noopener noreferrer">View on GitHub</a></p>
  `;
}

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
