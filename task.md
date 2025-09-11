# 🔹 Interactive to fetching and displaying GitHub PRs or Issues

**Goal:** Build an interactive test scenario to fetch and display GitHub PRs or Issues.

**Steps:**

1. **Input Repository**

   * User provides a GitHub repository URL (e.g., `https://github.com/user/repo`)
   * Validate the URL format. If invalid, show a popup error specifying the problem.

2. **Select Data Type**

   * Provide a dropdown menu: `["Pull Requests", "Issues"]`
   * User selects one.

3. **Fetch List**

   * Fetch the list of PRs or Issues from GitHub via GitHub API
   * Display a second dropdown with **titles** (or numbers + titles) of PRs/Issues

4. **Show Details**

   * When a PR/Issue is selected, display its details on the page:

     * Title
     * Author
     * Status (open/closed/merged)
     * Created date / Updated date
     * Body content

5. **Extra Validation (Optional for Agent Testing)**

   * Limit API calls to avoid exceeding rate limits
   * Allow user to select multiple PRs/Issues and show combined summary
   * Highlight PRs/Issues that meet certain conditions (e.g., have label `bug`)

---

### **UI Components**

* **Input field**: GitHub repo URL
* **Dropdown #1**: PR or Issue selection
* **Dropdown #2**: List of PRs/Issues
* **Detail panel**: Display selected PR/Issue info

