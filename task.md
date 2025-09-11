# 🔹 Interactive GitHub PR/Issue Viewer (with Node.js Proxy)

**Goal:** Build an interactive test scenario to fetch and display GitHub PRs or Issues **directly from GitHub API**, using a Node.js server to solve CORS issues. No simulated data.

**Setup:**

1. Use **Node.js** to run a local server: `node server.js`
2. The server will act as a proxy for GitHub API requests to avoid CORS restrictions.
3. Frontend interacts with the Node.js server to fetch data.

**Steps:**

1. **Input Repository**

   * User provides a GitHub repository URL (e.g., `https://github.com/user/repo`)
   * Validate the URL format. If invalid, show a popup error specifying the problem.

2. **Select Data Type**

   * Provide a dropdown menu: `["Pull Requests", "Issues"]`
   * User selects one.

3. **Fetch List via Node Proxy**

   * Frontend calls the Node.js server, which fetches the PRs/Issues from GitHub API.
   * Display a second dropdown with **titles** (or numbers + titles) of PRs/Issues.

4. **Show Details**

   * When a PR/Issue is selected, display its details on the page:

     * Title
     * Author
     * Status (open/closed/merged)
     * Created date / Updated date
     * Body content

5. **Extra Validation (Optional for Agent Testing)**

   * Limit API calls to avoid exceeding GitHub rate limits.
   * Allow user to select multiple PRs/Issues and show combined summary.
   * Highlight PRs/Issues that meet certain conditions (e.g., have label `bug`).

---

### **UI Components**

* **Input field**: GitHub repo URL
* **Dropdown #1**: PR or Issue selection
* **Dropdown #2**: List of PRs/Issues fetched from API
* **Detail panel**: Display selected PR/Issue info

---

### **Node.js Server Requirements**

* Create a simple **Express.js** server in `server.js`.
* Server routes example:

  ```js
  // GET /api/prs?repo=user/repo
  // GET /api/issues?repo=user/repo
  ```
* Server should fetch GitHub API data and return JSON to frontend.
* Handle errors and rate limits gracefully.



## How to run

- Install dependencies: `npm install`
- Start the server: `npm start`
- Open http://localhost:3000 in your browser
- Enter a repo URL like `https://github.com/ghcpd/joseph_test_repo`
- Select "Pull Requests" or "Issues", click "Fetch List", then choose an item to view details

Notes:
- To increase GitHub API rate limits, you can set a token: `export GITHUB_TOKEN=YOUR_TOKEN`
- The server proxies calls to the GitHub API to avoid CORS and returns JSON.
- Errors (including rate limits or network blocks) are displayed clearly in the UI.
