// DOM elements
const repoUrlInput = document.getElementById('repoUrl');
const dataTypeSelect = document.getElementById('dataType');
const fetchBtn = document.getElementById('fetchBtn');
const itemsSection = document.getElementById('itemsSection');
const itemSelect = document.getElementById('itemSelect');
const detailsPanel = document.getElementById('detailsPanel');
const detailsContent = document.getElementById('detailsContent');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorModal = document.getElementById('errorModal');
const errorMessage = document.getElementById('errorMessage');
const closeModal = document.querySelector('.close');

// Store fetched data
let currentData = [];

// Event listeners
fetchBtn.addEventListener('click', handleFetchData);
itemSelect.addEventListener('change', handleItemSelection);
closeModal.addEventListener('click', hideErrorModal);
window.addEventListener('click', (e) => {
    if (e.target === errorModal) {
        hideErrorModal();
    }
});

// Validate GitHub repository URL
function validateRepoUrl(url) {
    if (!url || url.trim() === '') {
        return { valid: false, error: 'Repository URL cannot be empty' };
    }

    // Allow both full URLs and user/repo format
    const fullUrlPattern = /^https?:\/\/(www\.)?github\.com\/[^\/]+\/[^\/]+/;
    const shortPattern = /^[^\/]+\/[^\/]+$/;

    if (!fullUrlPattern.test(url) && !shortPattern.test(url)) {
        return { 
            valid: false, 
            error: 'Invalid repository format. Use either "https://github.com/user/repo" or "user/repo"' 
        };
    }

    return { valid: true };
}

// Show error modal
function showError(message) {
    errorMessage.textContent = message;
    errorModal.style.display = 'block';
}

// Hide error modal
function hideErrorModal() {
    errorModal.style.display = 'none';
}

// Show loading indicator
function showLoading() {
    loadingIndicator.style.display = 'block';
    fetchBtn.disabled = true;
}

// Hide loading indicator
function hideLoading() {
    loadingIndicator.style.display = 'none';
    fetchBtn.disabled = false;
}

// Fetch data from the server
async function handleFetchData() {
    const repoUrl = repoUrlInput.value.trim();
    const dataType = dataTypeSelect.value;

    // Validate repository URL
    const validation = validateRepoUrl(repoUrl);
    if (!validation.valid) {
        showError(validation.error);
        return;
    }

    // Check if data type is selected
    if (!dataType) {
        showError('Please select a data type (Pull Requests or Issues)');
        return;
    }

    // Show loading indicator
    showLoading();

    // Hide previous results
    itemsSection.style.display = 'none';
    detailsPanel.style.display = 'none';

    try {
        const endpoint = dataType === 'prs' ? '/api/prs' : '/api/issues';
        const response = await fetch(`${endpoint}?repo=${encodeURIComponent(repoUrl)}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch data');
        }

        const data = await response.json();
        currentData = data;

        if (data.length === 0) {
            showError(`No ${dataType === 'prs' ? 'pull requests' : 'issues'} found in this repository`);
            hideLoading();
            return;
        }

        // Populate the items dropdown
        populateItemsDropdown(data, dataType);
        
        // Show items section
        itemsSection.style.display = 'block';
        
        hideLoading();
    } catch (error) {
        console.error('Error fetching data:', error);
        showError(error.message);
        hideLoading();
    }
}

// Populate items dropdown
function populateItemsDropdown(items, dataType) {
    // Clear existing options
    itemSelect.innerHTML = '<option value="">-- Select Item --</option>';

    // Add items to dropdown
    items.forEach((item, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = `#${item.number} - ${item.title}`;
        itemSelect.appendChild(option);
    });
}

// Handle item selection
function handleItemSelection() {
    const selectedIndex = itemSelect.value;

    if (selectedIndex === '') {
        detailsPanel.style.display = 'none';
        return;
    }

    const item = currentData[selectedIndex];
    displayItemDetails(item);
}

// Display item details
function displayItemDetails(item) {
    // Determine status display
    let statusText = item.state;
    let statusClass = `status-${item.state}`;
    
    if (item.merged) {
        statusText = 'merged';
        statusClass = 'status-merged';
    }

    // Format dates
    const createdDate = new Date(item.created_at).toLocaleString();
    const updatedDate = new Date(item.updated_at).toLocaleString();

    // Build labels HTML
    let labelsHtml = '';
    if (item.labels && item.labels.length > 0) {
        labelsHtml = item.labels.map(label => {
            const labelClass = label.toLowerCase() === 'bug' ? 'label-badge label-bug' : 'label-badge';
            return `<span class="${labelClass}">${label}</span>`;
        }).join('');
    } else {
        labelsHtml = '<span class="detail-value">None</span>';
    }

    // Build details HTML
    const detailsHtml = `
        <div class="detail-item">
            <div class="detail-label">Title</div>
            <div class="detail-value">${escapeHtml(item.title)}</div>
        </div>

        <div class="detail-item">
            <div class="detail-label">Number</div>
            <div class="detail-value">#${item.number}</div>
        </div>

        <div class="detail-item">
            <div class="detail-label">Author</div>
            <div class="detail-value">${escapeHtml(item.author)}</div>
        </div>

        <div class="detail-item">
            <div class="detail-label">Status</div>
            <div class="detail-value">
                <span class="status-badge ${statusClass}">${statusText}</span>
            </div>
        </div>

        <div class="detail-item">
            <div class="detail-label">Created</div>
            <div class="detail-value">${createdDate}</div>
        </div>

        <div class="detail-item">
            <div class="detail-label">Updated</div>
            <div class="detail-value">${updatedDate}</div>
        </div>

        <div class="detail-item">
            <div class="detail-label">Labels</div>
            <div class="detail-value">${labelsHtml}</div>
        </div>

        <div class="detail-item">
            <div class="detail-label">Description</div>
            <div class="body-content">${escapeHtml(item.body)}</div>
        </div>

        <div class="detail-item">
            <div class="detail-label">GitHub Link</div>
            <div class="detail-value">
                <a href="${item.html_url}" target="_blank" rel="noopener noreferrer">${item.html_url}</a>
            </div>
        </div>
    `;

    detailsContent.innerHTML = detailsHtml;
    detailsPanel.style.display = 'block';
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
