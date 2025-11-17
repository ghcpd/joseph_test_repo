# Flask PR/Issue Dashboard

## Overview
This project provides a Flask-based dashboard for exploring pull requests (PRs) and issues harvested from the GitHub API. The app loads data from four JSONL files at startup, exposes interactive tables powered by DataTables, renders aggregated charts with Plotly, and offers JSON APIs for reuse in other tools.

## Data Sources
- `input_data/pr_issue_single.jsonl` – PR search results with a `closing_issue` link
- `input_data/pr_detail.jsonl` – Detailed pull request metadata
- `input_data/issue_detail.jsonl` – Detailed issue metadata
- `output_data/merged_data.jsonl` – Integrated PR/issue dataset produced by `integrate_pr_issue.py`

Each file is parsed line-by-line into dedicated in-memory structures indexed by repo and identifying numbers to support fast lookups across datasets.

## Application Structure
```
app.py                 # Flask application entry point and routes
data/manager.py        # Data loading, enrichment, and aggregation logic
static/css/styles.css  # Custom styling
static/js/main.js      # DataTables initialization and dataset switching
templates/             # Jinja templates for layout, detail, and charts
input_data/, output_data/ # JSONL source files
```

## Key Features
- Summary cards showing dataset record counts
- Dataset tabs with searchable/sortable DataTables-powered tables
- Linked detail pages with related PR/issue data
- Visualization page with Plotly charts and repository filtering
- JSON API endpoints for each dataset, ready for client-side chart data
- Simple in-memory caching of data aggregations for responsive visualizations

## Getting Started
1. Create and activate a virtual environment (optional):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask app:
   ```bash
   flask --app app run
   ```
4. Open `http://127.0.0.1:5000/` in your browser to access the dashboard. The visualization page is available at `/visualize`.

## API Endpoints
- `GET /api/pr_issue`
- `GET /api/pr_detail`
- `GET /api/issue_detail`
- `GET /api/merged_data`

Each endpoint accepts an optional `repo` query parameter for filtering (e.g., `/api/merged_data?repo=exampleorg/sample-repo`) and returns the filtered dataset as JSON.

## Tests
Run the automated tests with:
```bash
pytest
```
The suite covers data loading, core endpoints, and visualization routing.

## Implementation Checklist
- [x] Analyze repository structure and requirements
- [x] Prepare sample data files and directory structure
- [x] Implement Flask application with data loading and route structure
- [x] Create templates and static assets for UI, charts, and tables
- [x] Provide API endpoints, caching, requirements, and documentation
- [x] Add automated tests for data loading and endpoints
- [x] Run tests, manual verification, and capture UI screenshot
- [x] Final review, update README, and finalize deliverables
