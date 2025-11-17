# Testing Instructions

## Automated Tests

This repository does not include an automated testing infrastructure for the browser-based UI. A minimal static implementation was required, so no unit or integration tests were added.

## Manual Verification

1. Start a simple HTTP server inside the project directory:
   ```bash
   python -m http.server 8000
   ```
2. Open the application in a browser at [http://localhost:8000/index.html](http://localhost:8000/index.html).
3. Provide a GitHub repository URL (e.g., `https://github.com/octocat/hello-world`).
4. Choose **Pull Requests** or **Issues** and click **Fetch List**.
5. After the list populates, select an item to view its details in the panel.
6. Items labelled `bug` show a 🐞 indicator in the list for quick identification.

If cross-origin requests are blocked in the environment, fetching data may fail with an alert. In that case, run the app from a local browser with internet access to observe the complete behaviour.
