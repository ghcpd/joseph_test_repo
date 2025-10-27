// Mock data for demonstration purposes
const mockData = {
    'microsoft/vscode': {
        pulls: [
            {
                number: 12345,
                title: "Fix: Resolve issue with editor performance on large files",
                user: {
                    login: "developer1",
                    avatar_url: "https://avatars.githubusercontent.com/u/1?v=4"
                },
                state: "open",
                created_at: "2024-01-15T10:30:00Z",
                updated_at: "2024-01-16T14:20:00Z",
                body: "This PR addresses performance issues when working with large files in the editor. The changes include:\n\n- Optimized text rendering\n- Improved memory management\n- Better handling of syntax highlighting",
                html_url: "https://github.com/microsoft/vscode/pull/12345",
                merged_at: null,
                labels: []
            },
            {
                number: 12344,
                title: "Feature: Add new theme support for extensions",
                user: {
                    login: "designer2",
                    avatar_url: "https://avatars.githubusercontent.com/u/2?v=4"
                },
                state: "closed",
                created_at: "2024-01-10T09:15:00Z",
                updated_at: "2024-01-14T16:45:00Z",
                body: "This PR introduces support for custom themes in extensions, allowing developers to create more personalized coding environments.",
                html_url: "https://github.com/microsoft/vscode/pull/12344",
                merged_at: "2024-01-14T16:45:00Z",
                labels: []
            }
        ],
        issues: [
            {
                number: 54321,
                title: "Bug: Syntax highlighting broken for TypeScript files",
                user: {
                    login: "reporter1",
                    avatar_url: "https://avatars.githubusercontent.com/u/3?v=4"
                },
                state: "open",
                created_at: "2024-01-12T08:45:00Z",
                updated_at: "2024-01-15T11:30:00Z",
                body: "Syntax highlighting is not working correctly for TypeScript files with certain decorators. The issue appears when using class decorators in combination with generic types.",
                html_url: "https://github.com/microsoft/vscode/issues/54321",
                merged_at: null,
                labels: [
                    { name: "bug", color: "d73a4a" },
                    { name: "typescript", color: "0052cc" }
                ]
            },
            {
                number: 54320,
                title: "Feature Request: Add support for custom keybindings export",
                user: {
                    login: "poweruser",
                    avatar_url: "https://avatars.githubusercontent.com/u/4?v=4"
                },
                state: "closed",
                created_at: "2024-01-05T15:20:00Z",
                updated_at: "2024-01-13T12:10:00Z",
                body: "It would be great to have the ability to export and import custom keybinding configurations to easily share setups between different installations.",
                html_url: "https://github.com/microsoft/vscode/issues/54320",
                merged_at: null,
                labels: [
                    { name: "feature-request", color: "a2eeef" },
                    { name: "keybindings", color: "0e8a16" }
                ]
            }
        ]
    }
};

// Modify the GitHubFetcher class to use mock data for demonstration
const originalFetchItems = GitHubFetcher.prototype.fetchItems;

GitHubFetcher.prototype.fetchItems = function(type) {
    const listSection = document.querySelector('.list-section');
    const loading = document.getElementById('loading');
    const itemList = document.getElementById('item-list');
    const fetchError = document.getElementById('fetch-error');
    
    // Show loading state
    listSection.style.display = 'block';
    loading.style.display = 'block';
    itemList.innerHTML = '<option value="">-- Loading... --</option>';
    this.hideError('fetch-error');
    
    // Simulate API delay
    setTimeout(() => {
        try {
            const { owner, repo } = this.currentRepo;
            const repoKey = `${owner}/${repo}`;
            
            if (mockData[repoKey] && mockData[repoKey][type]) {
                const items = mockData[repoKey][type];
                this.populateItemList(items, type);
            } else {
                // Try to call original method for real API (will likely fail due to CORS)
                originalFetchItems.call(this, type);
            }
            
        } catch (error) {
            console.error('Mock fetch error:', error);
            this.showError('fetch-error', 'Demo data not available for this repository');
            itemList.innerHTML = '<option value="">-- Demo data not available --</option>';
        } finally {
            loading.style.display = 'none';
        }
    }, 1000); // 1 second delay to show loading
};

console.log('Demo mode enabled with mock data for microsoft/vscode');