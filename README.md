# PR & Issue Insight Dashboard

This repository contains a Flask application that visualizes relationships between pull requests and issues drawn from four JSONL datasets. The interface offers searchable tables, detail pages with cross-links, and Plotly-powered visualizations.

## Project Structure

```
.
├── app.py
├── data/
│   ├── __init__.py
│   └── loader.py
├── input_data/
│   ├── issue_detail.jsonl
│   ├── pr_detail.jsonl
│   └── pr_issue_single.jsonl
├── output_data/
│   └── merged_data.jsonl
├── static/
│   ├── css/style.css
│   └── js/main.js
├── templates/
│   ├── base.html
│   ├── detail.html
│   ├── home.html
│   └── visualize.html
├── tests/
│   └── test_app.py
├── requirements.txt
└── README.md
```

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the server**

   ```bash
   export FLASK_APP=app.py
   flask run
   ```

   The dashboard is available at http://127.0.0.1:5000/.

3. **Run the tests**

   ```bash
   pytest
   ```

## Features

- Loads and indexes four JSONL datasets at startup.
- Responsive Bootstrap pages with DataTables search and sorting.
- Detail views with cross-dataset links to related PRs and issues.
- Plotly charts for repository-level metrics with optional repository filtering.
- JSON API endpoints (e.g., `/api/pr_detail`) for programmatic access to the data.
- Cached aggregation helpers for quick chart rendering.

## API Endpoints

- `/api/pr_issue` – Pull request search results
- `/api/pr_detail` – Pull request details
- `/api/issue_detail` – Issue details
- `/api/merged_data` – Integrated PR/issue data

Each endpoint accepts an optional `repo` query parameter to filter results to a single repository.

## Notes

- Sample datasets are included under `input_data/` and `output_data/` for local experimentation.
- Plotly.js, Bootstrap, and DataTables are loaded from CDN sources for convenience.
