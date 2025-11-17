# GitHub Pull Request & Issue Explorer

This simple web application provides an interactive way to inspect pull requests or issues for any public GitHub repository. Enter the repository URL, choose whether to view pull requests or issues, and browse their details in a clean interface.

## Features

- Validates repository URLs and surfaces actionable errors in the UI.
- Fetches pull requests or issues directly from the GitHub REST API.
- Uses dropdown lists to browse available items and inspect their metadata.
- Displays author, status, creation/update dates, and body content for each item.
- Highlights entries tagged with the `bug` label and caches results to reduce repeated API calls.

## Getting Started

### Prerequisites

- Node.js 18 or later (only required for running the optional dev server via `npm start`).
- A stable internet connection to reach the GitHub REST API.

### Quick Start

1. Install dependencies (none are required beyond Node, so this step can be skipped).
2. Launch a static web server:

   ```bash
   npm start
   ```

   The script uses `http-server` via `npx` to serve the application at <http://localhost:5173>.

   Alternatively, any static file server works:

   ```bash
   python -m http.server 5173
   ```

3. Open the served page in your browser and follow the on-screen instructions:
   - Paste a GitHub repository URL (e.g., `https://github.com/owner/repo`).
   - Select whether to view pull requests or issues.
   - Choose an entry from the list to display its detailed information.

## Testing

Automated tests are not yet configured for this repo. The `npm test` command prints a notice and exits successfully. Manual verification through the UI is recommended when making changes.

## Notes on API Usage

- Only public repositories are supported unless you modify the client to include an authenticated request.
- Results are cached per repository and selection to avoid unnecessary API calls, helping stay within GitHub's rate limits.
- The interface only retrieves the first 100 pull requests or issues for a repository.
