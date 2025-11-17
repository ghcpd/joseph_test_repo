# PR & Issue Dashboard

This project is a Flask-based analytics dashboard that showcases relationships between GitHub pull requests and issues using sample JSONL data. It demonstrates how the datasets connect and provides interactive tables and charts for exploration.

## Features

- Loads four JSONL datasets at startup and caches them in memory.
- Dashboard with summary counts and DataTables-powered searchable tables for all datasets.
- Detail pages for each record with related data links.
- Visualization page with Chart.js charts for repositories, timelines, closing issues, PRs by month, and issue labels.
- Optional repository filtering for charts via query parameters.
- JSON API endpoints exposing raw and aggregated data with cached results.

## Project Structure

```
.
├── app.py
├── data
│   ├── input_data
│   │   ├── pr_detail.jsonl
│   │   ├── pr_issue_single.jsonl
│   │   └── issue_detail.jsonl
│   └── output_data
│       └── merged_data.jsonl
├── templates
│   ├── base.html
│   ├── detail.html
│   ├── index.html
│   └── visualize.html
└── static
    └── styles.css
```

## Getting Started

### Prerequisites

- Python 3.9+

### Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:

   ```bash
   python app.py
   ```

3. Open your browser and navigate to `http://127.0.0.1:5000` to view the dashboard.

### Manual Verification

- Visit the homepage to see dataset summaries and interactive tables.
- Navigate to detail pages to inspect individual records and related entries.
- Explore the visualization page and optionally filter by repository.

## API Endpoints

Each dataset has an API endpoint serving both data and aggregations:

- `GET /api/pr_issue`
- `GET /api/pr_detail`
- `GET /api/issue_detail`
- `GET /api/merged_data`

Optional query parameters:

- `repo`: filter by repository (e.g., `repo=example/cool-project`).
- `aggregation`: specify aggregated data to retrieve:
  - `merged_data`: `repo_counts`, `timeline`
  - `pr_issue`: `closing_issue`
  - `pr_detail`: `monthly_counts`
  - `issue_detail`: `label_counts`

Example:

```
GET /api/merged_data?aggregation=repo_counts&repo=example/cool-project
```

## Notes

- The included JSONL data is sample data to demonstrate functionality.
- Chart data is cached to avoid recalculating aggregations on repeated requests.
- Client-side tables use DataTables.js for searching, sorting, and pagination.
