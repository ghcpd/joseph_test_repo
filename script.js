class GitHubViewer {
    constructor() {
        this.currentRepo = '';
        this.currentData = [];
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Repository validation
        document.getElementById('validateRepo').addEventListener('click', () => {
            this.validateRepository();
        });

        // Data fetching
        document.getElementById('fetchData').addEventListener('click', () => {
            this.fetchData();
        });

        // Item selection
        document.getElementById('itemSelect').addEventListener('change', (e) => {
            this.displayItemDetails(e.target.value);
        });

        // Modal close
        document.querySelector('.close').addEventListener('click', () => {
            this.closeModal();
        });

        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('errorModal');
            if (e.target === modal) {
                this.closeModal();
            }
        });

        // Enter key support for repo URL
        document.getElementById('repoUrl').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.validateRepository();
            }
        });
    }

    validateRepository() {
        const repoUrl = document.getElementById('repoUrl').value.trim();
        const statusElement = document.getElementById('repoStatus');

        if (!repoUrl) {
            this.showError('Please enter a GitHub repository URL');
            return;
        }

        // Extract repo from URL
        const repo = this.extractRepoFromUrl(repoUrl);
        if (!repo) {
            this.showError('Invalid GitHub repository URL format. Expected: https://github.com/user/repo');
            return;
        }

        // Show success and enable next step
        this.currentRepo = repo;
        statusElement.className = 'status-message success';
        statusElement.textContent = `✓ Repository validated: ${repo}`;
        
        // Enable data type selection
        document.getElementById('dataType').disabled = false;
        this.enableFetchButton();
    }

    extractRepoFromUrl(url) {
        // Handle various GitHub URL formats
        const patterns = [
            /^https?:\/\/github\.com\/([^\/]+\/[^\/]+)\/?$/,
            /^([^\/]+\/[^\/]+)$/
        ];

        for (const pattern of patterns) {
            const match = url.match(pattern);
            if (match) {
                const repo = match[1].replace(/\.git$/, '');
                // Validate repo format
                if (repo.match(/^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/)) {
                    return repo;
                }
            }
        }
        return null;
    }

    enableFetchButton() {
        const dataType = document.getElementById('dataType').value;
        const fetchButton = document.getElementById('fetchData');
        fetchButton.disabled = !dataType || !this.currentRepo;
    }

    async fetchData() {
        const dataType = document.getElementById('dataType').value;
        const statusElement = document.getElementById('fetchStatus');
        const itemSelect = document.getElementById('itemSelect');

        if (!dataType || !this.currentRepo) {
            this.showError('Please validate repository and select data type first');
            return;
        }

        // Show loading state
        statusElement.className = 'status-message loading';
        statusElement.textContent = `🔄 Fetching ${dataType === 'prs' ? 'Pull Requests' : 'Issues'}...`;
        
        document.getElementById('fetchData').disabled = true;

        try {
            const endpoint = dataType === 'prs' ? '/api/prs' : '/api/issues';
            const response = await fetch(`${endpoint}?repo=${encodeURIComponent(this.currentRepo)}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            const data = await response.json();
            this.currentData = data;

            // Update UI
            this.populateItemSelect(data, dataType);
            
            statusElement.className = 'status-message success';
            statusElement.textContent = `✓ Found ${data.length} ${dataType === 'prs' ? 'Pull Request(s)' : 'Issue(s)'}`;

        } catch (error) {
            console.error('Fetch error:', error);
            statusElement.className = 'status-message error';
            statusElement.textContent = `✗ Error: ${error.message}`;
            
            // Clear item select
            itemSelect.innerHTML = '<option value="">No items loaded...</option>';
            itemSelect.disabled = true;
            
            this.clearDetails();
        } finally {
            document.getElementById('fetchData').disabled = false;
        }
    }

    populateItemSelect(data, dataType) {
        const itemSelect = document.getElementById('itemSelect');
        
        if (data.length === 0) {
            itemSelect.innerHTML = `<option value="">No ${dataType === 'prs' ? 'Pull Requests' : 'Issues'} found</option>`;
            itemSelect.disabled = true;
            this.clearDetails();
            return;
        }

        itemSelect.innerHTML = '<option value="">Select an item...</option>';
        
        data.forEach((item, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `#${item.number}: ${item.title}`;
            itemSelect.appendChild(option);
        });

        itemSelect.disabled = false;
        this.clearDetails();
    }

    displayItemDetails(selectedIndex) {
        const detailsPanel = document.getElementById('detailsPanel');
        
        if (selectedIndex === '' || !this.currentData[selectedIndex]) {
            this.clearDetails();
            return;
        }

        const item = this.currentData[selectedIndex];
        
        detailsPanel.innerHTML = `
            <div class="details-content">
                <h3>${this.escapeHtml(item.title)}</h3>
                
                <div class="details-meta">
                    <div class="meta-item">
                        <span class="meta-label">Number</span>
                        <span class="meta-value">#${item.number}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Author</span>
                        <span class="meta-value">${this.escapeHtml(item.user.login)}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Status</span>
                        <span class="meta-value">
                            <span class="status-badge status-${item.state}${item.merged ? ' status-merged' : ''}">${item.state}${item.merged ? ' (merged)' : ''}</span>
                        </span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Created</span>
                        <span class="meta-value">${this.formatDate(item.created_at)}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Updated</span>
                        <span class="meta-value">${this.formatDate(item.updated_at)}</span>
                    </div>
                    ${item.labels && item.labels.length > 0 ? `
                    <div class="meta-item">
                        <span class="meta-label">Labels</span>
                        <span class="meta-value">${item.labels.map(label => `<span class="label" style="background-color: #${label.color}; color: ${this.getContrastColor(label.color)}; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px;">${this.escapeHtml(label.name)}</span>`).join('')}</span>
                    </div>
                    ` : ''}
                </div>
                
                <div class="details-body">
                    <h4>Description</h4>
                    ${item.body ? this.formatMarkdown(item.body) : '<p><em>No description provided</em></p>'}
                </div>
            </div>
        `;
    }

    clearDetails() {
        const detailsPanel = document.getElementById('detailsPanel');
        detailsPanel.innerHTML = '<p class="placeholder">Select an item to view its details</p>';
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    formatMarkdown(text) {
        // Basic markdown-to-HTML conversion
        let html = this.escapeHtml(text);
        
        // Convert line breaks
        html = html.replace(/\n/g, '<br>');
        
        // Convert code blocks
        html = html.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');
        
        // Convert inline code
        html = html.replace(/`([^`]+)`/g, '<code style="background-color: #f1f3f4; padding: 2px 4px; border-radius: 3px;">$1</code>');
        
        // Convert bold text
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Convert italic text
        html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Convert links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
        
        return `<div>${html}</div>`;
    }

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
        
        // Calculate brightness
        const brightness = (r * 299 + g * 587 + b * 114) / 1000;
        
        return brightness > 128 ? '#000000' : '#ffffff';
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorModal').style.display = 'block';
        
        // Clear any success states
        const repoStatus = document.getElementById('repoStatus');
        if (repoStatus.classList.contains('success')) {
            repoStatus.className = 'status-message error';
            repoStatus.textContent = `✗ ${message}`;
        }
    }

    closeModal() {
        document.getElementById('errorModal').style.display = 'none';
    }
}

// Enable/disable fetch button when data type changes
document.getElementById('dataType').addEventListener('change', function() {
    const viewer = window.githubViewer;
    if (viewer) {
        viewer.enableFetchButton();
    }
});

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.githubViewer = new GitHubViewer();
});