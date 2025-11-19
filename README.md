# GitHub PR/Issue Viewer

An interactive web application to fetch and display GitHub Pull Requests or Issues from any public repository.

## Features

- **Repository URL Input**: Enter any GitHub repository URL
- **URL Validation**: Validates the format and shows error popups for invalid URLs
- **Data Type Selection**: Choose between Pull Requests or Issues via dropdown
- **Dynamic List**: Fetches and displays a list of PRs/Issues from the GitHub API
- **Detailed View**: Shows comprehensive details including:
  - Title
  - Number
  - Author
  - Status (open/closed/merged)
  - Created and Updated dates
  - Labels (with special highlighting for 'bug' labels)
  - Body content
- **Error Handling**: Graceful error handling for API rate limits and invalid repositories
- **Responsive Design**: Modern, clean UI with smooth animations

## How to Use

1. Open `github-viewer.html` in a web browser
2. Enter a GitHub repository URL (e.g., `https://github.com/microsoft/vscode`)
3. Select whether you want to view "Pull Requests" or "Issues"
4. Click "Fetch List" to retrieve the data
5. Select an item from the dropdown to view its details

## Technical Details

- Built with vanilla HTML, CSS, and JavaScript
- Uses GitHub REST API v3
- No external dependencies required
- Fetches up to 50 items per request
- Includes rate limit handling

## Notes

- The application uses the public GitHub API, which has rate limits (60 requests per hour for unauthenticated users)
- Only works with public repositories
- Supports all repository states (open, closed, merged)
