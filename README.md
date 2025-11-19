# PR & Issue Dashboard

A Flask-based dashboard for exploring pull requests, issues, and merged records from GitHub API exports. The application demonstrates how JSONL datasets can be combined, inspected, and visualized with interactive tables (DataTables) and charts (Plotly).

## Features

- Loads GitHub-related JSONL files at startup and keeps them in memory for fast responses.
- Responsive Bootstrap interface with dataset summaries and DataTables-powered search and sorting.
- Detail pages for every record with direct navigation to related issues, pull requests, merged data, and search results.
- `/visualize` page showing interactive Plotly charts for all datasets with optional repository filtering.
- JSON API endpoints (`/api/<dataset_name>`) for use in client-side visualizations or integrations.
- In-memory caching of chart aggregations to keep the visualization page responsive.

## Project Structure

```
.
├── app.py                 # Flask application
├── data
│   ├── input_data
│   │   ├── pr_detail.jsonl
│   │   ├── pr_issue_single.jsonl
│   │   └── issue_detail.jsonl
│   └── output_data
│       └── merged_data.jsonl
├── static
│   ├── css
│   │   └── styles.css
│   └── js
│       └── app.js
├── templates
│   ├── base.html
│   ├── detail.html
│   ├── index.html
│   └── visualize.html
└── requirements.txt
```

The JSONL files contain a small curated dataset showing how issues and pull requests intersect. `integrate_pr_issue.py` can be used to regenerate the merged dataset from the inputs.

## Getting Started

1. **Create a virtual environment (recommended):**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**

   ```bash
   flask --app app run
   ```

   Alternatively, you can run `python app.py` to start the development server with debug mode enabled.

4. **Explore the UI:**

   - **Dashboard (`/`)**: Overview cards, dataset tabs, and searchable tables that link to record details.
   - **Detail pages**: Accessible via the “View” buttons or clickable rows for each dataset.
   - **Visualization (`/visualize`)**: Plotly charts for merged, search, PR, and issue datasets with optional repository filters.
   - **APIs**: JSON responses available at `/api/pr_issue`, `/api/pr_detail`, `/api/issue_detail`, and `/api/merged_data`. Append `?repo=<owner/repo>` to filter.

## Data Notes

- The JSONL files are stored under `data/` and are loaded entirely into memory at startup for fast routing.
- Each dataset record contains a `_record_id` field used for linking to detail pages.
- `app.py` automatically adds helper fields (such as `closing_issue_count`) to simplify visualization and table rendering.

## Regenerating the merged dataset

If you modify the input files, you can regenerate `data/output_data/merged_data.jsonl` with:

```bash
python integrate_pr_issue.py
```

This script reads from the three input JSONL files, matches pull requests to their related issues, and writes a new merged dataset.

## Screenshots

Run the app and navigate to `http://127.0.0.1:5000` to browse the dashboard and visualize the data. A sample screenshot is included in the PR to illustrate the UI.
