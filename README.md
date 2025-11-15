# GitHub PR & Issue Explorer

This repository contains a lightweight static interface for exploring pull requests or issues from any public GitHub repository.

## Running the interactive scenario

1. Start a local web server in the project root (for example using Python):
   ```bash
   python3 -m http.server 8000
   ```
2. Open your browser to `http://localhost:8000/index.html`.
3. Enter a GitHub repository URL in the form `https://github.com/OWNER/REPOSITORY`.
4. Choose whether to explore pull requests or issues and press **Fetch List**.
5. Select one or multiple entries from the results to view detailed information and combined summaries.

> **Note:** GitHub’s unauthenticated API is rate-limited. If you receive a rate limit error, wait before making additional requests or provide an access token by modifying the fetch request headers.
