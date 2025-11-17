# GitHub PR / Issue Viewer

This project provides an interactive interface for browsing pull requests or issues from a GitHub repository. A Node.js Express server proxies requests to the GitHub API to avoid CORS restrictions, and a simple frontend allows users to select repositories and inspect individual items.

## Features

- Repository input with validation for full GitHub URLs (`https://github.com/user/repo`) or `owner/repo` format.
- Dropdown to toggle between pull requests and issues.
- Dynamic list populated from the GitHub API via the local proxy.
- Detail view displaying title, author, status (including merged state for PRs), creation/update timestamps, labels, and body content.
- Optional enhancements:
  - Multiple selection support that produces a summary of selected items.
  - Visual highlights for entries containing the `bug` label.
- Lightweight caching to minimize repeated API calls and reduce the chance of rate limit exhaustion.

## Getting Started

1. Install dependencies:

   ```bash
   npm install
   ```

2. Run the development server:

   ```bash
   npm start
   ```

   The application will be available at [http://localhost:4173](http://localhost:4173) by default. To run on a different port (for example `3000`), specify it explicitly:

   ```bash
   PORT=3000 npm start
   ```

3. (Optional) Provide a GitHub personal access token to increase rate limits:

   ```bash
   export GITHUB_TOKEN=your_token
   npm start
   ```

## Testing

Run unit tests with:

```bash
npm test
```

Tests mock the GitHub API and verify repository validation, error handling, and proxy behavior.

## Usage Notes

- The application fetches up to 50 pull requests or issues per request.
- When multi-selecting several entries, a summary is shown above the detail panel.
- Rate limit errors from GitHub are surfaced to the user with friendly messaging.
