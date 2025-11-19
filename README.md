# GitHub PR/Issue Viewer

An interactive web application to fetch and display GitHub Pull Requests and Issues directly from the GitHub API, using a Node.js server to solve CORS issues.

## Features

- **Repository Input**: Enter a GitHub repository URL or `user/repo` format
- **Data Type Selection**: Choose between Pull Requests or Issues
- **Real-time Fetching**: Fetch data directly from GitHub API via Node.js proxy
- **Detailed View**: Display comprehensive information including:
  - Title, Number, Author
  - Status (open/closed/merged for PRs)
  - Created and Updated dates
  - Labels (with special highlighting for "bug" labels)
  - Full description/body content
  - Direct link to GitHub
- **Error Handling**: Validation and user-friendly error messages
- **Rate Limit Handling**: Graceful handling of GitHub API rate limits

## Setup

### Prerequisites

- Node.js (v12 or higher)
- npm (comes with Node.js)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ghcpd/joseph_test_repo.git
cd joseph_test_repo
```

2. Install dependencies:
```bash
npm install
```

## Usage

1. Start the Node.js server:
```bash
npm start
```
or
```bash
node server.js
```

2. Open your web browser and navigate to:
```
http://localhost:3000
```

3. Use the application:
   - Enter a GitHub repository URL (e.g., `https://github.com/facebook/react` or `facebook/react`)
   - Select "Pull Requests" or "Issues" from the dropdown
   - Click "Fetch Data"
   - Select an item from the list to view details

## API Endpoints

The Node.js server provides two endpoints:

### GET /api/prs
Fetch pull requests for a repository.

**Query Parameters:**
- `repo` (required): GitHub repository in format `user/repo` or full URL

**Example:**
```
http://localhost:3000/api/prs?repo=facebook/react
```

### GET /api/issues
Fetch issues for a repository.

**Query Parameters:**
- `repo` (required): GitHub repository in format `user/repo` or full URL

**Example:**
```
http://localhost:3000/api/issues?repo=facebook/react
```

## Project Structure

```
.
├── server.js          # Express.js server with GitHub API proxy
├── package.json       # Node.js dependencies and scripts
├── public/
│   ├── index.html    # Main HTML page
│   ├── styles.css    # CSS styling
│   └── app.js        # Frontend JavaScript logic
└── README.md         # This file
```

## Error Handling

The application handles various error scenarios:

- **Invalid URL Format**: Shows a popup explaining the correct format
- **Repository Not Found**: Displays a user-friendly error message
- **Rate Limit Exceeded**: Informs the user about GitHub API rate limits
- **Network Errors**: Catches and displays connection issues

## Notes

- The application fetches up to 100 items per request (GitHub API default)
- For unauthenticated requests, GitHub API rate limit is 60 requests per hour
- Pull Requests show a "merged" status if applicable
- Issues are filtered to exclude pull requests (GitHub API returns PRs as issues)

## License

ISC
