// GitHub PR/Issue Fetcher JavaScript
class GitHubFetcher {
    constructor() {
        this.apiBase = 'https://api.github.com';
        this.currentRepo = null;
        this.apiCallCount = 0;
        this.maxApiCalls = 50; // Conservative limit
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // URL validation button
        document.getElementById('validate-btn').addEventListener('click', () => {
            this.validateRepository();
        });

        // Enter key on URL input
        document.getElementById('repo-url').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.validateRepository();
            }
        });

        // Data type selection
        document.getElementById('data-type').addEventListener('change', (e) => {
            if (e.target.value) {
                this.fetchItems(e.target.value);
            }
        });

        // Item selection
        document.getElementById('item-list').addEventListener('change', (e) => {
            if (e.target.value) {
                this.showItemDetails(JSON.parse(e.target.value));
            }
        });

        // Modal close
        document.querySelector('.close').addEventListener('click', () => {
            this.hideModal();
        });

        // Click outside modal to close
        document.getElementById('error-modal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.hideModal();
            }
        });
    }

    validateRepository() {
        const urlInput = document.getElementById('repo-url');
        const url = urlInput.value.trim();
        
        // Clear previous errors
        this.hideError('url-error');
        
        if (!url) {
            this.showError('url-error', 'Please enter a GitHub repository URL');
            return;
        }

        // Validate GitHub URL format
        const githubUrlPattern = /^https:\/\/github\.com\/([^\/]+)\/([^\/]+)\/?$/;
        const match = url.match(githubUrlPattern);
        
        if (!match) {
            this.showModal('Invalid URL Format', 
                'Please enter a valid GitHub repository URL in the format: https://github.com/user/repo');
            return;
        }

        const [, owner, repo] = match;
        this.currentRepo = { owner, repo, url };
        
        // Show success and enable next step
        this.showSelectionSection();
    }

    showSelectionSection() {
        document.querySelector('.selection-section').style.display = 'block';
        
        // Reset subsequent sections
        document.querySelector('.list-section').style.display = 'none';
        document.querySelector('.details-section').style.display = 'none';
        
        // Reset dropdowns
        document.getElementById('data-type').value = '';
        document.getElementById('item-list').innerHTML = '<option value="">-- Select Type First --</option>';
    }

    async fetchItems(type) {
        if (this.apiCallCount >= this.maxApiCalls) {
            this.showRateLimitWarning();
            return;
        }

        const listSection = document.querySelector('.list-section');
        const loading = document.getElementById('loading');
        const itemList = document.getElementById('item-list');
        const fetchError = document.getElementById('fetch-error');
        
        // Show loading state
        listSection.style.display = 'block';
        loading.style.display = 'block';
        itemList.innerHTML = '<option value="">-- Loading... --</option>';
        this.hideError('fetch-error');
        
        try {
            const { owner, repo } = this.currentRepo;
            const endpoint = `${this.apiBase}/repos/${owner}/${repo}/${type}`;
            
            this.apiCallCount++;
            const response = await fetch(endpoint);
            
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Repository not found or does not exist');
                } else if (response.status === 403) {
                    throw new Error('API rate limit exceeded. Please try again later.');
                } else {
                    throw new Error(`Failed to fetch data: ${response.status} ${response.statusText}`);
                }
            }
            
            const items = await response.json();
            
            if (items.length === 0) {
                itemList.innerHTML = `<option value="">-- No ${type === 'pulls' ? 'Pull Requests' : 'Issues'} found --</option>`;
            } else {
                this.populateItemList(items, type);
            }
            
        } catch (error) {
            console.error('Fetch error:', error);
            this.showError('fetch-error', error.message);
            itemList.innerHTML = '<option value="">-- Error loading data --</option>';
        } finally {
            loading.style.display = 'none';
        }
    }

    populateItemList(items, type) {
        const itemList = document.getElementById('item-list');
        
        // Create options
        const options = items.map(item => {
            const displayText = `#${item.number} - ${item.title}`;
            const itemData = {
                number: item.number,
                title: item.title,
                user: item.user,
                state: item.state,
                created_at: item.created_at,
                updated_at: item.updated_at,
                body: item.body || 'No description provided',
                html_url: item.html_url,
                merged_at: item.merged_at, // For PRs
                labels: item.labels || [], // For issues
                type: type
            };
            
            return `<option value='${JSON.stringify(itemData)}'>${displayText}</option>`;
        });
        
        itemList.innerHTML = [
            '<option value="">-- Select an item --</option>',
            ...options
        ].join('');
    }

    showItemDetails(item) {
        const detailsSection = document.querySelector('.details-section');
        const detailsPanel = document.getElementById('item-details');
        
        // Format dates
        const createdDate = new Date(item.created_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const updatedDate = new Date(item.updated_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // Determine status with proper styling
        let status = item.state;
        let statusClass = item.state;
        
        if (item.type === 'pulls' && item.merged_at) {
            status = 'merged';
            statusClass = 'merged';
        }
        
        // Build labels section for issues
        let labelsHtml = '';
        if (item.labels && item.labels.length > 0) {
            const labelElements = item.labels.map(label => 
                `<span class="label" style="background-color: #${label.color}; color: ${this.getContrastColor(label.color)}; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-right: 4px;">${label.name}</span>`
            ).join('');
            labelsHtml = `
                <div class="detail-item">
                    <div class="detail-label">Labels:</div>
                    <div class="detail-value">${labelElements}</div>
                </div>
            `;
        }
        
        detailsPanel.innerHTML = `
            <div class="detail-item">
                <div class="detail-label">Title:</div>
                <div class="detail-value title">${this.escapeHtml(item.title)}</div>
            </div>
            
            <div class="detail-item">
                <div class="detail-label">Author:</div>
                <div class="detail-value">
                    <img src="${item.user.avatar_url}" alt="${item.user.login}" style="width: 20px; height: 20px; border-radius: 50%; vertical-align: middle; margin-right: 8px;">
                    <strong>${this.escapeHtml(item.user.login)}</strong>
                </div>
            </div>
            
            <div class="detail-item">
                <div class="detail-label">Status:</div>
                <div class="detail-value">
                    <span class="status ${statusClass}">${status}</span>
                </div>
            </div>
            
            <div class="detail-item">
                <div class="detail-label">Created:</div>
                <div class="detail-value">${createdDate}</div>
            </div>
            
            <div class="detail-item">
                <div class="detail-label">Updated:</div>
                <div class="detail-value">${updatedDate}</div>
            </div>
            
            ${labelsHtml}
            
            <div class="detail-item">
                <div class="detail-label">Description:</div>
                <div class="detail-value body">${this.escapeHtml(item.body)}</div>
            </div>
            
            <div class="detail-item">
                <div class="detail-label">Link:</div>
                <div class="detail-value">
                    <a href="${item.html_url}" target="_blank" rel="noopener noreferrer">View on GitHub →</a>
                </div>
            </div>
        `;
        
        detailsSection.style.display = 'block';
        
        // Scroll to details
        detailsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Utility functions
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getContrastColor(hexColor) {
        // Convert hex to RGB
        const r = parseInt(hexColor.substr(0, 2), 16);
        const g = parseInt(hexColor.substr(2, 2), 16);
        const b = parseInt(hexColor.substr(4, 2), 16);
        
        // Calculate luminance
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        
        return luminance > 0.5 ? '#000000' : '#FFFFFF';
    }

    showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }

    hideError(elementId) {
        const errorElement = document.getElementById(elementId);
        errorElement.style.display = 'none';
    }

    showModal(title, message) {
        document.getElementById('modal-error-text').textContent = message;
        document.getElementById('error-modal').style.display = 'flex';
    }

    hideModal() {
        document.getElementById('error-modal').style.display = 'none';
    }

    showRateLimitWarning() {
        document.getElementById('rate-limit-warning').style.display = 'block';
        setTimeout(() => {
            document.getElementById('rate-limit-warning').style.display = 'none';
        }, 5000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new GitHubFetcher();
});

// Add some helpful console information
console.log('🔹 GitHub PR/Issue Fetcher loaded successfully!');
console.log('Enter a GitHub repository URL to get started.');